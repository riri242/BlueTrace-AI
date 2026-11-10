"""Deterministic backward integration tests with synthetic ocean grids."""
import numpy as np
import pandas as pd
import pytest
import xarray as xr

from bluetrace_ml.trajectory import (
    MarineGrid, advance_backward, backtrack, score_trace,
)


def ocean(speed=0.1, *, missing=False):
    times = pd.date_range("2020-01-01T00:00Z", periods=36, freq="h").tz_localize(None)
    lat = np.array([35.0, 36.0, 37.0])
    lon = np.array([-123.0, -122.0, -121.0])
    shape = (len(times), len(lat), len(lon))
    u = np.full(shape, speed)
    if missing:
        u[0, 1, 1] = np.nan
    current = xr.Dataset(
        {"uo": (("time", "latitude", "longitude"), u),
         "vo": (("time", "latitude", "longitude"), np.zeros(shape))},
        coords={"time": times, "latitude": lat, "longitude": lon},
    )
    waves = xr.Dataset(
        {"VSDX": (("time", "latitude", "longitude"), np.zeros(shape)),
         "VSDY": (("time", "latitude", "longitude"), np.zeros(shape))},
        coords={"time": times, "latitude": lat, "longitude": lon},
    )
    return MarineGrid(current, waves)


def test_backward_step_decreases_longitude_for_eastward_current():
    lat, lon = advance_backward(36.0, -122.0, u=0.5, v=0)
    assert lat == pytest.approx(36.0)
    assert lon < -122.0


def test_24hour_trace_has_25_points_with_correct_end_time():
    grid = ocean()
    result = backtrack(36.0, -122.0, "2020-01-02T00:00:00Z", grid)
    assert result.status == "complete"
    assert result.steps == 24
    assert len(result.path) == 25
    assert result.path[-1]["time"] == "2020-01-01T00:00:00+00:00"
    assert result.path[-1]["longitude"] < -122.0
    assert score_trace(result, result.path[-1]["latitude"], result.path[-1]["longitude"]) == pytest.approx(0)


def test_trace_exits_grid_instead_of_extrapolating():
    grid = ocean(speed=25.0)
    result = backtrack(36.0, -122.0, "2020-01-02T00:00:00Z", grid)
    assert result.status == "incomplete"
    assert result.steps < 24
    assert "outside cached marine grid" in result.reason


def test_grid_rejects_future_only_measurement():
    grid = ocean()
    with pytest.raises(ValueError, match="at or before"):
        grid.velocity("2019-12-30T00:00:00Z", 36.0, -122.0)


def test_windage_requires_supplied_wind():
    with pytest.raises(ValueError, match="wind time series"):
        backtrack(36.0, -122.0, "2020-01-02T00:00:00Z", ocean(), windage=0.01)


def test_trace_does_not_evaluate_incomplete_path():
    result = backtrack(36.0, -122.0, "2020-01-02T00:00:00Z", ocean(speed=25.0))
    assert score_trace(result, 36.0, -122.0) is None
