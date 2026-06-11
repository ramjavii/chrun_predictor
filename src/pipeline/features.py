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
    features = events.copy()
    for transform in config.get("transforms", []):
        name = transform["name"]
        func = _get_transform(name)
        if func:
            kwargs = {k: v for k, v in transform.items() if k != "name"}
            features = func(features, **kwargs)
    return features


def _get_transform(name: str) -> Callable | None:
    registry = {
        "count_events": _count_events,
        "recency_days": _recency_days,
    }
    return registry.get(name)


def _count_events(df: pd.DataFrame, group_by: str = "customer_id", window_days: int = 30) -> pd.DataFrame: ...


def _recency_days(
    df: pd.DataFrame, timestamp_col: str = "timestamp", group_by: str = "customer_id"
) -> pd.DataFrame: ...
