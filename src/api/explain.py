import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/explain", tags=["explain"])


@router.get("/{customer_id}")
async def explain_customer(customer_id: str, session: AsyncSession = Depends(get_session)):
    return {"customer_id": customer_id, "status": "not_implemented"}
