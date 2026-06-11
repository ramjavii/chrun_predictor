from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from src.pipeline.features import (
    _avg_time_between_events,
    _count_events,
    _recency_days,
    build_features,
    load_feature_config,
)


def test_load_feature_config(tmp_path):
    config_file = tmp_path / "features.yaml"
    config_file.write_text("transforms:\n  - name: count_events\n    window_days: 30\n")
    config = load_feature_config(config_file)
    assert config["transforms"][0]["name"] == "count_events"
    assert config["transforms"][0]["window_days"] == 30


class TestCountEvents:
    def test_counts_events_in_window(self):
        now = datetime.now(UTC)
        df = pd.DataFrame(
            {
                "customer_id": ["c1", "c1", "c1", "c2"],
                "timestamp": [now, now - timedelta(days=5), now - timedelta(days=40), now],
            }
        )
        result = _count_events(df, group_by="customer_id", window_days=30)
        assert list(result["count_events_30d"]) == [2, 1]

    def test_all_events_when_no_window(self):
        df = pd.DataFrame(
            {
                "customer_id": ["c1", "c1", "c2"],
                "timestamp": [datetime.now(UTC)] * 3,
            }
        )
        result = _count_events(df, group_by="customer_id")
        assert list(result["count_events"]) == [2, 1]


class TestRecencyDays:
    def test_recency_from_now(self):
        now = datetime.now(UTC)
        df = pd.DataFrame(
            {
                "customer_id": ["c1", "c2"],
                "timestamp": [now - timedelta(days=3), now - timedelta(days=10)],
            }
        )
        result = _recency_days(df, timestamp_col="timestamp", group_by="customer_id")
        assert result["recency_days"].iloc[0] == pytest.approx(0, abs=0.1)
        assert result["recency_days"].iloc[1] == pytest.approx(7, abs=0.1)


class TestAvgTimeBetweenEvents:
    def test_average_gap(self):
        now = datetime.now(UTC)
        df = pd.DataFrame(
            {
                "customer_id": ["c1", "c1", "c1", "c2", "c2"],
                "timestamp": [now, now - timedelta(days=2), now - timedelta(days=6), now, now - timedelta(days=5)],
            }
        )
        result = _avg_time_between_events(df, group_by="customer_id")
        # c1: gaps of 2 and 4 days → avg=3 days
        assert result["avg_time_between_events"].iloc[0] == pytest.approx(3.0, abs=0.5)
        # c2: only 1 gap of 5 days
        assert result["avg_time_between_events"].iloc[1] == pytest.approx(5.0, abs=0.5)


class TestBuildFeatures:
    def test_pipe_chain(self):
        now = datetime.now(UTC)
        df = pd.DataFrame(
            {
                "customer_id": ["c1", "c1", "c2"],
                "timestamp": [now, now - timedelta(days=3), now - timedelta(days=10)],
            }
        )
        config = {
            "transforms": [
                {"name": "count_events", "group_by": "customer_id", "window_days": 30},
                {"name": "recency_days", "group_by": "customer_id"},
            ]
        }
        result = build_features(df, config)
        assert "count_events_30d" in result.columns
        assert "recency_days" in result.columns
        assert len(result) == 2  # one row per customer
