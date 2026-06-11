import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.models.database import Customer, Feature
from src.models.schemas import FeatureResponse
from src.pipeline.feature_store import compute_features_for_customer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/features", tags=["features"])


@router.get("/{customer_id}")
async def get_features(
    customer_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[FeatureResponse]:
    customer = (await session.execute(select(Customer).where(Customer.external_id == customer_id))).scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    features = (await session.execute(select(Feature).where(Feature.customer_id == customer.id))).scalars().all()

    return [
        FeatureResponse(
            feature_name=f.feature_name,
            feature_value=f.feature_value,
            window_start=f.window_start,
            window_end=f.window_end,
        )
        for f in features
    ]


@router.post("/compute", status_code=status.HTTP_201_CREATED)
async def compute_features(
    customer_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    if customer_id:
        features = await compute_features_for_customer(session, customer_id)
        await session.commit()
        return {"customer_id": customer_id, "features_computed": len(features)}
    raise HTTPException(status_code=400, detail="customer_id is required")
