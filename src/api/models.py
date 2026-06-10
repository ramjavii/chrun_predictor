import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("")
async def list_models(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}


@router.post("/register")
async def register_model(session: AsyncSession = Depends(get_session)):
    return {"status": "not_implemented"}
