import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.pipeline.predict import predict_batch, predict_single

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/predict", tags=["predict"])


@router.get("/{customer_id}")
async def predict_single_endpoint(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await predict_single(session, customer_id)
    if result is None:
        return {"customer_id": customer_id, "score": None, "status": "no_model_or_features"}
    return result


@router.post("/batch")
async def predict_batch_endpoint(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    results = await predict_batch(session)
    await session.commit()
    return results
