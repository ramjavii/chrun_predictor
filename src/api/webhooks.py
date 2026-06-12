import logging
from datetime import UTC, datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_session
from src.models.database import Customer, Event

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

STRIPE_EVENT_MAP: dict[str, str] = {
    "customer.subscription.created": "subscription_started",
    "customer.subscription.updated": "subscription_changed",
    "customer.subscription.deleted": "subscription_cancelled",
    "invoice.payment_succeeded": "payment_succeeded",
    "invoice.payment_failed": "payment_failed",
}


async def _resolve_customer(session: AsyncSession, external_id: str) -> Customer:
    result = await session.execute(select(Customer).where(Customer.external_id == external_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        customer = Customer(external_id=external_id)
        session.add(customer)
        await session.flush()
    return customer


def _extract_customer_id(data: dict, event_type: str) -> str | None:
    customer = data.get("customer")
    if isinstance(customer, str):
        return customer
    if isinstance(customer, dict):
        return customer.get("id")
    return None


def _build_properties(data: dict, stripe_event_id: str, event_type: str) -> dict:
    props: dict = {
        "stripe_event_id": stripe_event_id,
        "stripe_event_type": event_type,
    }

    if event_type == "customer.subscription.created":
        plan = data.get("items", {}).get("data", [{}])[0].get("plan", {})
        props["plan"] = plan.get("nickname")
        props["amount"] = plan.get("amount")
        props["interval"] = plan.get("interval")

    elif event_type == "customer.subscription.updated":
        props["status"] = data.get("status")
        props["cancel_at_period_end"] = data.get("cancel_at_period_end")

    elif event_type == "customer.subscription.deleted":
        props["canceled_at"] = data.get("canceled_at")

    elif event_type in ("invoice.payment_succeeded", "invoice.payment_failed"):
        props["amount"] = data.get("amount_paid") or data.get("amount_due") or data.get("total")
        props["invoice_id"] = data.get("id")
        if event_type == "invoice.payment_failed":
            props["attempt_count"] = data.get("attempt_count", 0)
            pi = data.get("payment_intent", {})
            if isinstance(pi, dict):
                error = pi.get("last_payment_error", {})
                if error:
                    props["failure_code"] = error.get("code")
                    props["failure_message"] = error.get("message")

    return {k: v for k, v in props.items() if v is not None}


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if not settings.stripe_webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        raise HTTPException(status_code=501, detail="Stripe integration not configured")

    body = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(body, sig_header, settings.stripe_webhook_secret)
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None

    raw_type: str = event.get("type", "")
    ids_type = STRIPE_EVENT_MAP.get(raw_type)

    if ids_type is None:
        logger.info("Ignoring unsupported Stripe event type: %s", raw_type)
        return {"status": "ignored", "event_type": raw_type}

    data = event.get("data", {}).get("object", {})
    customer_id = _extract_customer_id(data, raw_type)

    if not customer_id:
        logger.warning("No customer ID in Stripe event %s", event.get("id"))
        return {"status": "ignored", "reason": "no_customer"}

    properties = _build_properties(data, event.get("id", ""), raw_type)

    try:
        customer = await _resolve_customer(session, customer_id)
        event_obj = Event(
            customer_id=customer.id,
            event_type=ids_type,
            properties=properties,
            timestamp=datetime.fromtimestamp(data.get("created", event.get("created", 0)), tz=UTC),
        )
        session.add(event_obj)
        await session.commit()
        logger.info("Stripe event %s mapped to %s for customer %s", raw_type, ids_type, customer_id)
        return {"status": "processed", "event_type": ids_type, "customer_id": customer_id}
    except Exception:
        await session.rollback()
        logger.exception("Failed to process Stripe event %s", event.get("id"))
        raise HTTPException(status_code=500, detail="Failed to process webhook") from None
