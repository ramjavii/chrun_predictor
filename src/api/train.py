import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.pipeline.train import train_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/train", tags=["train"])


@router.post("")
async def trigger_training(session: AsyncSession = Depends(get_session)) -> dict:
    result = await train_pipeline(session)
    await session.commit()
    return result
