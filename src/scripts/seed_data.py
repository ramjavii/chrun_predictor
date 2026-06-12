"""
Generate synthetic customer event data to exercise the full churn pipeline.

Usage:
    python -m src.scripts.seed_data --customers 50
    python -m src.scripts.seed_data --customers 20 --train
"""

import argparse
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from random import Random

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.models.database import Customer, Event

logger = logging.getLogger(__name__)

EVENT_TYPES = [
    "page_view",
    "login",
    "logout",
    "feature_used",
    "settings_changed",
    "report_exported",
    "integration_connected",
    "ticket_opened",
    "api_call",
]


def _make_events(rng, customer_id, days_of_history):
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=days_of_history)
    n_events = rng.randint(5, 200)
    timestamps = sorted(cutoff + timedelta(seconds=rng.randint(0, days_of_history * 86400)) for _ in range(n_events))
    churned = rng.random() < 0.4
    if churned and len(timestamps) > 3:
        churn_window = timedelta(days=rng.randint(90, 120))
        last_ok = now - churn_window
        timestamps = [t for t in timestamps if t < last_ok]
        if len(timestamps) < 2:
            timestamps = [now - timedelta(days=rng.randint(0, 30)) for _ in range(rng.randint(5, 20))]
    events = []
    for ts in timestamps:
        event_type = rng.choice(EVENT_TYPES)
        properties = None
        if event_type == "page_view":
            properties = {"page": rng.choice(["/home", "/pricing", "/docs", "/settings", "/dashboard"])}
        elif event_type == "integration_connected":
            properties = {"service": rng.choice(["slack", "github", "jira", "stripe"])}
        elif event_type == "ticket_opened":
            properties = {"priority": rng.choice(["low", "medium", "high"])}
        elif event_type == "api_call":
            properties = {"endpoint": rng.choice(["/v1/predict", "/v1/events", "/v1/models"])}
        events.append(
            Event(
                customer_id=customer_id,
                event_type=event_type,
                properties=properties,
                timestamp=ts,
            )
        )
    return events


async def seed(engine, n_customers=20, train_after=False):
    factory = async_sessionmaker(engine, class_=AsyncSession)

    async with engine.begin() as conn:
        from src.models.database import Base

        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        await session.execute(text("TRUNCATE predictions, features, events, customers, model_metadata CASCADE"))
        await session.commit()

    rng = Random(42)

    async with factory() as session:
        for i in range(n_customers):
            external_id = f"cus_{i:04d}"
            days_history = rng.randint(60, 365)
            cust = Customer(external_id=external_id)
            session.add(cust)
            await session.flush()
            events = _make_events(rng, cust.id, days_history)
            for ev in events:
                session.add(ev)
            logger.info("  %s -- %d events, %d days history", external_id, len(events), days_history)

        await session.commit()
        logger.info("Seeded %d customers with synthetic events.", n_customers)

    if train_after:
        from src.pipeline.feature_store import compute_features_for_all
        from src.pipeline.train import train_pipeline

        async with factory() as session:
            logger.info("Computing features for all customers...")
            feat_counts = await compute_features_for_all(session)
            total = sum(feat_counts.values())
            logger.info("Computed %d features across %d customers.", total, len(feat_counts))
            logger.info("Training model...")
            result = await train_pipeline(session)
            await session.commit()
            m = result.get("metrics", {})
            logger.info(
                "Model %s -- accuracy=%.4f, n_samples=%d, n_features=%d",
                result.get("version", "?"),
                m.get("accuracy", 0),
                m.get("n_samples", 0),
                m.get("n_features", 0),
            )

    logger.info("Done.")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
    parser = argparse.ArgumentParser(description="Seed synthetic customer data for the churn pipeline.")
    parser.add_argument("--customers", type=int, default=20, help="Number of synthetic customers (default: 20)")
    parser.add_argument("--train", action="store_true", help="Compute features and train a model after seeding")
    args = parser.parse_args()
    engine = create_async_engine(settings.database_url, echo=False)
    asyncio.run(seed(engine, n_customers=args.customers, train_after=args.train))


if __name__ == "__main__":
    main()
