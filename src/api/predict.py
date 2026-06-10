import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/predict", tags=["predict"])


@router.get("/{customer_id}")
async def predict_single(customer_id: str, session: AsyncSession = Depends(get_session)):
    return {"customer_id": customer_id, "score": None, "status": "not_implemented"}


@router.post("/batch")
async def predict_batch(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}
