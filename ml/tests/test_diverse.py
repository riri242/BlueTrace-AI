"""Offline validation of bounded, diverse NOAA sampling."""
import pandas as pd
import pytest

from scripts.build_diverse import select_windows, describe_selection


def observations():
    rows = []
    for year in (2010, 2011):
        for month in (1, 6):
            for drifter in (11, 22, 33):
                for hour in range(4):
                    rows.append({
                        "ID": f"{year}-{month}-{drifter}",
                        "time": pd.Timestamp(year=year, month=month, day=10,
                                             hour=hour, tz="UTC"),
                        "latitude": 36.0 + drifter / 100,
                        "longitude": -122 + hour / 100,
                    })
    return pd.DataFrame(rows)


def test_multiple_years_and_windows_diversify_drifters():
    batches = select_windows(observations(), [2010, 2011],
                             windows_per_year=2, rows_per_window=6)
    report = describe_selection(batches)
    assert report["selected_windows"] == 4
    assert report["unique_drifters"] == 12
    assert report["selected_rows"] == 24
    assert all(window["latitude_span"] <= 2 for window in report["windows"])
    assert all(window["longitude_span"] <= 2 for window in report["windows"])


def test_empty_year_skipped_without_failure():
    batches = select_windows(observations(), [2005, 2011], windows_per_year=1)
    assert len(batches) == 1
    assert batches[0]["year"] == 2011


def test_invalid_limits_rejected():
    with pytest.raises(ValueError, match="sampling limits"):
        select_windows(observations(), [2010], windows_per_year=0)
