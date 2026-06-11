import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.models.database import Customer, Event
from src.models.schemas import EventBatchResponse, EventCreate, EventResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/events", tags=["events"])


async def _resolve_customer(session: AsyncSession, external_id: str) -> Customer:
    result = await session.execute(select(Customer).where(Customer.external_id == external_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = Customer(external_id=external_id)
        session.add(customer)
        await session.flush()
    return customer


def _event_to_response(event: Event, external_id: str) -> EventResponse:
    return EventResponse(
        id=event.id,
        customer_id=event.customer_id,
        customer_external_id=external_id,
        event_type=event.event_type,
        properties=event.properties,
        timestamp=event.timestamp,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_event(
    body: EventCreate,
    session: AsyncSession = Depends(get_session),
) -> EventResponse:
    try:
        customer = await _resolve_customer(session, body.customer_external_id)
        event = Event(
            customer_id=customer.id,
            event_type=body.event_type,
            properties=body.properties,
            timestamp=body.timestamp or datetime.now(UTC),
        )
        session.add(event)
        await session.flush()
        response = _event_to_response(event, customer.external_id)
        await session.commit()
        return response
    except Exception:
        await session.rollback()
        raise


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def ingest_events_batch(
    body: list[EventCreate],
    session: AsyncSession = Depends(get_session),
) -> EventBatchResponse:
    responses: list[EventResponse] = []
    try:
        for item in body:
            customer = await _resolve_customer(session, item.customer_external_id)
            event = Event(
                customer_id=customer.id,
                event_type=item.event_type,
                properties=item.properties,
                timestamp=item.timestamp or datetime.now(UTC),
            )
            session.add(event)
            await session.flush()
            responses.append(_event_to_response(event, customer.external_id))
        await session.commit()
        return EventBatchResponse(events=responses)
    except Exception:
        await session.rollback()
        raise
