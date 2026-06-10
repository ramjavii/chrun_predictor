import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/train", tags=["train"])


@router.post("")
async def trigger_training(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}
