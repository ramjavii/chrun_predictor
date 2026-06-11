import logging
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def load_feature_config(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def build_features(events: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = events[["customer_id"]].drop_duplicates().reset_index(drop=True)
    for transform in config.get("transforms", []):
        name = transform["name"]
        func = _get_transform(name)
        if func is None:
            logger.warning("Unknown transform: %s", name)
            continue
        kwargs = {k: v for k, v in transform.items() if k != "name"}
        result = func(events, **kwargs)
        features = features.merge(result, on="customer_id", how="left")
    return features


def _get_transform(name: str) -> Callable | None:
    registry: dict[str, Callable] = {
        "count_events": _count_events,
        "recency_days": _recency_days,
        "avg_time_between_events": _avg_time_between_events,
    }
    return registry.get(name)


def _count_events(df: pd.DataFrame, group_by: str = "customer_id", window_days: int | None = None) -> pd.DataFrame:
    col = f"count_events{'' if window_days is None else f'_{window_days}d'}"
    data = df.copy()
    if window_days is not None:
        cutoff = data["timestamp"].max() - pd.Timedelta(days=window_days)
        data = data[data["timestamp"] >= cutoff]
    counts = data.groupby(group_by).size().reset_index(name=col)
    return counts


def _recency_days(df: pd.DataFrame, timestamp_col: str = "timestamp", group_by: str = "customer_id") -> pd.DataFrame:
    now = df[timestamp_col].max()
    recency = df.groupby(group_by)[timestamp_col].max().reset_index()
    recency["recency_days"] = (now - recency[timestamp_col]).dt.total_seconds() / 86400
    recency = recency.drop(columns=[timestamp_col])
    return recency


def _avg_time_between_events(df: pd.DataFrame, group_by: str = "customer_id") -> pd.DataFrame:
    data = df.sort_values([group_by, "timestamp"])
    data["prev_timestamp"] = data.groupby(group_by)["timestamp"].shift(1)
    data["gap_days"] = (data["timestamp"] - data["prev_timestamp"]).dt.total_seconds() / 86400
    avg_gaps = data.groupby(group_by)["gap_days"].mean().reset_index()
    avg_gaps = avg_gaps.rename(columns={"gap_days": "avg_time_between_events"})
    return avg_gaps.fillna(0)
