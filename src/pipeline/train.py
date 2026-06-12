import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from xgboost import XGBClassifier

from src.models.database import Feature, ModelMetadata

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/data/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CHURN_WINDOW_DAYS = 90


async def build_training_dataset(session: AsyncSession) -> pd.DataFrame:
    features = (
        await session.execute(
            select(
                Feature.customer_id,
                Feature.feature_name,
                Feature.feature_value,
            )
        )
    ).all()

    if not features:
        return pd.DataFrame()

    df = pd.DataFrame(features, columns=["customer_id", "feature_name", "feature_value"])

    pivot = df.pivot_table(
        index="customer_id",
        columns="feature_name",
        values="feature_value",
        aggfunc="first",
    ).reset_index()
    pivot.columns.name = None

    last_events = (
        await session.execute(
            select(
                Feature.customer_id,
                Feature.window_end,
            )
        )
    ).all()
    last_df = pd.DataFrame(last_events, columns=["customer_id", "window_end"])
    last_times = last_df.groupby("customer_id")["window_end"].max().reset_index()

    now = datetime.now(UTC)

    def _is_churned(ts):
        ts = ts.replace(tzinfo=UTC) if ts.tzinfo is None else ts
        return 1 if now - ts > timedelta(days=CHURN_WINDOW_DAYS) else 0

    last_times["churned"] = last_times["window_end"].apply(_is_churned)

    dataset = pivot.merge(last_times[["customer_id", "churned"]], on="customer_id", how="left")
    return dataset


async def train_pipeline(session: AsyncSession) -> dict:
    logger.info("Building training dataset...")
    dataset = await build_training_dataset(session)
    if dataset.empty:
        logger.warning("No training data available")
        return {"status": "skipped", "reason": "no_data"}

    feature_cols = sorted([c for c in dataset.columns if c not in ("customer_id", "churned")])
    x_mat = dataset[feature_cols].fillna(0).values
    y = dataset["churned"].values

    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss",
    )
    model.fit(x_mat, y)

    version = datetime.now().strftime("v%Y%m%d_%H%M%S")
    model_path = MODEL_DIR / f"churn_{version}.json"
    model.save_model(str(model_path))

    y_pred = model.predict(x_mat)
    y_proba = model.predict_proba(x_mat)[:, 1]

    accuracy = float(np.mean(y_pred == y))
    proba_mean = float(np.mean(y_proba))

    metrics = {
        "accuracy": round(accuracy, 4),
        "avg_score": round(proba_mean, 4),
        "n_samples": int(len(y)),
        "n_features": int(x_mat.shape[1]),
        "churn_rate": float(y.mean()),
    }

    metadata = ModelMetadata(
        version=version,
        artifact_path=str(model_path),
        metrics=metrics,
        status="production",
    )
    session.add(metadata)
    await session.flush()

    logger.info("Model %s trained: accuracy=%.4f, samples=%d", version, accuracy, len(y))
    return {"status": "ok", "version": version, "metrics": metrics, "path": str(model_path)}
