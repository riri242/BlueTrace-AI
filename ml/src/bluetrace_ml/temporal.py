"""Causal-time-indexed retrospective environmental history at a fixed anchor.

All input timestamps must be UTC. Gridded GLORYS daily means are retrospective
products and cannot be assumed to have been published at their timestamp.
These routines never use grid time coordinates after the observation timestamp.
"""
import numpy as np
import pandas as pd


HOURS = 24
CHANNELS = ("wind_u", "wind_v", "current_u", "current_v", "stokes_u", "stokes_v")


def hourly_grid(observation_time, hours=HOURS):
    end = pd.Timestamp(observation_time)
    if end.tzinfo is None:
        raise ValueError("Observation time must include a timezone")
    end = end.tz_convert("UTC")
    if end.minute or end.second or end.microsecond or end.nanosecond:
        raise ValueError("Only hourly-aligned observations are supported")
    return pd.date_range(end=end, periods=hours, freq="h", tz="UTC")


def backward_match(source_times, values, target_times, max_age_hours):
    """Sample the latest available timestamp at or before each requested hour."""
    source = pd.DatetimeIndex(pd.to_datetime(source_times, utc=True))
    requested = pd.DatetimeIndex(pd.to_datetime(target_times, utc=True))
    values = np.asarray(values, dtype=float)
    if len(source) != len(values):
        raise ValueError("Source timestamps and values must have equal lengths")
    if source.has_duplicates or not source.is_monotonic_increasing:
        raise ValueError("Source timestamps must be strictly increasing")
    positions = source.searchsorted(requested, side="right") - 1
    result = np.full((len(requested),), np.nan)
    used = [None] * len(requested)
    for i, ix in enumerate(positions):
        if ix < 0:
            continue
        age = (requested[i] - source[ix]).total_seconds() / 3600
        if 0 <= age <= max_age_hours and np.isfinite(values[ix]):
            result[i] = values[ix]
            used[i] = source[ix].isoformat()
    return result, used


def summarize_history(series, observation_time):
    """Report temporal coverage and fixed-anchor component summaries."""
    hours = hourly_grid(observation_time)
    if not set(CHANNELS).issubset(series):
        raise ValueError("Missing temporal channels")
    counts = {}
    result = {"time": hours[-1].isoformat(), "temporal_hours": len(hours)}
    for channel in CHANNELS:
        array = np.asarray(series[channel], dtype=float)
        if len(array) != len(hours):
            raise ValueError(f"Expected 24 samples for {channel}")
        finite = np.isfinite(array)
        counts[channel] = int(finite.sum())
        result[channel + "_mean_24h"] = float(array.mean()) if finite.all() else None
        result[channel + "_std_24h"] = float(array.std()) if finite.all() else None
    result["valid_hours"] = int(np.isfinite(
        np.column_stack([series[c] for c in CHANNELS])).all(axis=1).sum())
    result["complete"] = result["valid_hours"] == HOURS
    result["channel_coverage_hours"] = counts
    if result["complete"]:
        # Fixed-anchor 24 * 1h displacement, not a simulated advected trajectory.
        result["backward_current_east_km"] = -float(np.sum(series["current_u"])) * 3.6
        result["backward_current_north_km"] = -float(np.sum(series["current_v"])) * 3.6
    else:
        result["backward_current_east_km"] = None
        result["backward_current_north_km"] = None
    return result
