"""Offline tests of pilot selection; no external services or credentials."""

import pandas as pd
import pytest

from scripts.build_pilot import select_observations


def observations():
    start = pd.Timestamp("2011-03-25T00:00:00Z")
    rows = []
    for drifter in range(1, 5):
        for hour in range(24):
            rows.append({
                "ID": drifter,
                "time": start + pd.Timedelta(hours=hour),
                "latitude": 36.0 + drifter * 0.1,
                "longitude": -122.0 + hour * 0.001,
            })
    return pd.DataFrame(rows)


def test_pilot_is_bounded_and_spatially_compact():
    sample = select_observations(observations(), sample_size=12, year=2011, days=3)
    assert len(sample) == 12
    assert sample["ID"].nunique() == 4
    assert sample["latitude"].max() - sample["latitude"].min() < 2
    assert sample["time"].dt.year.eq(2011).all()


def test_no_matching_year_fails_clearly():
    with pytest.raises(ValueError, match="No valid 24-hour"):
        select_observations(observations(), sample_size=12, year=1995, days=3)
