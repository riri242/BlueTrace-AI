"""Offline tests for temporal matching and 24h coverage safeguards."""
import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.temporal import (
    CHANNELS, backward_match, hourly_grid, summarize_history,
)


def test_hourly_grid_has_exactly_24_hours_ending_at_observation():
    time = pd.Timestamp("2022-05-04T13:00:00Z")
    times = hourly_grid(time)
    assert len(times) == 24
    assert times[0] == time - pd.Timedelta(hours=23)
    assert times[-1] == time


def test_backward_match_does_not_consume_future_values():
    times = pd.to_datetime([
        "2022-01-01T09:00:00Z",
        "2022-01-01T12:00:00Z",
    ])
    requested = pd.to_datetime([
        "2022-01-01T08:00:00Z",
        "2022-01-01T10:00:00Z",
        "2022-01-01T11:00:00Z",
        "2022-01-01T12:00:00Z",
    ])
    values, used = backward_match(times, [1.0, 9.0], requested, max_age_hours=2)
    assert np.isnan(values[0])
    assert values[1:].tolist() == [1.0, 1.0, 9.0]
    assert used[0] is None
    assert all(pd.Timestamp(s) <= time for s, time in zip(used[1:], requested[1:]))


def test_backward_match_rejects_stale_and_unsorted_sources():
    stamps = pd.to_datetime(["2011-01-01T00:00Z"])
    later = pd.to_datetime(["2011-01-01T04:00Z"])
    values, _ = backward_match(stamps, [5], later, max_age_hours=3)
    assert np.isnan(values[0])
    with pytest.raises(ValueError, match="strictly increasing"):
        backward_match(stamps.append(stamps), [1, 2], later, 3)


def test_temporal_history_integrates_hourly_current_only_when_complete():
    history = {name: np.ones(24) for name in CHANNELS}
    history["current_u"] = np.full(24, 0.5)
    result = summarize_history(history, "2022-05-04T13:00:00Z")
    assert result["complete"]
    assert result["backward_current_east_km"] == pytest.approx(-43.2)
    history["wind_v"][5] = np.nan
    missing = summarize_history(history, "2022-05-04T13:00:00Z")
    assert not missing["complete"]
    assert missing["valid_hours"] == 23
    assert missing["backward_current_east_km"] is None


def test_temporal_history_rejects_non_hour_aligned_observation():
    with pytest.raises(ValueError, match="hourly-aligned"):
        hourly_grid("2022-05-04T13:30:00Z")
