import logging
from pathlib import Path

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xgboost import XGBClassifier

from src.models.database import Customer, Feature, ModelMetadata, Prediction

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/data/models")


async def _load_latest_model(session: AsyncSession) -> XGBClassifier | None:
    result = await session.execute(
        select(ModelMetadata)
        .where(ModelMetadata.status == "production")
        .order_by(ModelMetadata.trained_at.desc())
        .limit(1)
    )
    meta = result.scalar_one_or_none()
    if meta is None:
        logger.warning("No production model found")
        return None

    model = XGBClassifier()
    model.load_model(meta.artifact_path)
    return model


async def _get_feature_vector(session: AsyncSession, customer_uuid) -> np.ndarray | None:
    features = (await session.execute(select(Feature).where(Feature.customer_id == customer_uuid))).scalars().all()

    if not features:
        return None

    row = {f.feature_name: f.feature_value for f in features}
    return np.array([v for _, v in sorted(row.items())])


async def predict_single(session: AsyncSession, customer_external_id: str) -> dict | None:
    model = await _load_latest_model(session)
    if model is None:
        return None

    customer = (
        await session.execute(select(Customer).where(Customer.external_id == customer_external_id))
    ).scalar_one_or_none()
    if customer is None:
        logger.warning("Customer %s not found", customer_external_id)
        return None

    x = await _get_feature_vector(session, customer.id)
    if x is None:
        logger.warning("No features for customer %s", customer_external_id)
        return None

    proba = model.predict_proba(x.reshape(1, -1))[0]
    score = float(proba[1])
    label = bool(score >= 0.5)

    pred = Prediction(
        customer_id=customer.id,
        model_version=getattr(model, "_version", "unknown"),
        score=score,
        threshold=0.5,
        predicted_label=label,
    )
    session.add(pred)
    await session.flush()

    return {
        "customer_id": customer_external_id,
        "score": score,
        "threshold": 0.5,
        "predicted_label": label,
        "prediction_id": pred.id,
    }


async def predict_batch(session: AsyncSession) -> list[dict]:
    customers = (await session.execute(select(Customer))).scalars().all()
    results = []
    for customer in customers:
        result = await predict_single(session, customer.external_id)
        if result:
            results.append(result)
    return results
