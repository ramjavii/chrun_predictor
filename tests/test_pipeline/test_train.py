from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from src.models.database import Customer, Feature, ModelMetadata
from src.pipeline.train import build_training_dataset, train_pipeline


@pytest.mark.asyncio
async def test_build_training_dataset_empty(db_session):
    dataset = await build_training_dataset(db_session)
    assert dataset.empty


@pytest.mark.asyncio
async def test_build_training_dataset_with_features(db_session):
    cust = Customer(external_id="train-c1")
    db_session.add(cust)
    await db_session.flush()

    now = datetime.now(UTC)
    db_session.add_all(
        [
            Feature(
                customer_id=cust.id,
                feature_name="count_events_30d",
                feature_value=5.0,
                window_start=now,
                window_end=now,
            ),
            Feature(
                customer_id=cust.id,
                feature_name="recency_days",
                feature_value=3.0,
                window_start=now,
                window_end=now,
            ),
        ]
    )
    await db_session.commit()

    dataset = await build_training_dataset(db_session)
    assert not dataset.empty
    assert "count_events_30d" in dataset.columns
    assert "recency_days" in dataset.columns


@pytest.mark.asyncio
async def test_train_pipeline_end_to_end(db_session):
    c1 = Customer(external_id="train-e2e-1")
    c2 = Customer(external_id="train-e2e-2")
    db_session.add_all([c1, c2])
    await db_session.flush()

    now = datetime.now(UTC)
    for c in (c1, c2):
        db_session.add_all(
            [
                Feature(
                    customer_id=c.id,
                    feature_name="count_events_30d",
                    feature_value=10.0,
                    window_start=now,
                    window_end=now,
                ),
                Feature(
                    customer_id=c.id,
                    feature_name="recency_days",
                    feature_value=5.0,
                    window_start=now,
                    window_end=now,
                ),
            ]
        )
    await db_session.commit()

    result = await train_pipeline(db_session)
    await db_session.commit()

    assert result["status"] == "ok"
    assert result["metrics"]["n_samples"] == 2

    models = (await db_session.execute(select(ModelMetadata))).scalars().all()
    assert len(models) >= 1
