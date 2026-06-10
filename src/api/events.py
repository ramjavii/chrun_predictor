import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("")
async def ingest_event(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}


@router.post("/batch")
async def ingest_events_batch(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}
