import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.database import Customer, Event, Feature
from src.pipeline.features import build_features, load_feature_config

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("configs/features.yaml")


async def compute_features_for_customer(
    session: AsyncSession,
    customer_id: str,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> list[Feature]:
    customer = (await session.execute(select(Customer).where(Customer.external_id == customer_id))).scalar_one_or_none()
    if customer is None:
        logger.warning("Customer %s not found", customer_id)
        return []

    events_result = await session.execute(
        select(Event).where(Event.customer_id == customer.id).order_by(Event.timestamp)
    )
    events = events_result.scalars().all()
    if not events:
        logger.info("No events for customer %s", customer_id)
        return []

    df = pd.DataFrame(
        [
            {
                "customer_id": str(customer.external_id),
                "event_type": e.event_type,
                "timestamp": e.timestamp,
            }
            for e in events
        ]
    )

    config = load_feature_config(config_path)
    features_df = build_features(df, config)

    now = pd.Timestamp.now(tz="UTC")
    window_start = now - pd.Timedelta(days=365)

    feature_records: list[Feature] = []
    for _, row in features_df.iterrows():
        for col in features_df.columns:
            if col == "customer_id":
                continue
            feature = Feature(
                customer_id=customer.id,
                feature_name=col,
                feature_value=float(row[col]),
                window_start=window_start.to_pydatetime(),
                window_end=now.to_pydatetime(),
            )
            session.add(feature)
            feature_records.append(feature)

    await session.flush()
    logger.info("Computed %d features for customer %s", len(feature_records), customer_id)
    return feature_records


async def compute_features_for_all(
    session: AsyncSession,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, int]:
    customers = (await session.execute(select(Customer))).scalars().all()
    results: dict[str, int] = {}
    for customer in customers:
        features = await compute_features_for_customer(session, customer.external_id, config_path)
        results[customer.external_id] = len(features)
    await session.commit()
    return results
