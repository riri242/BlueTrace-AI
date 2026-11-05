"""Inference-safe features: never use drifter-measured ve/vn or true previous coordinates."""

import numpy as np
import pandas as pd

ENVIRONMENT_FEATURES = (
    "wind_u", "wind_v", "current_u", "current_v", "stokes_u", "stokes_v"
)
LOCATION_FEATURES = ("latitude", "longitude", "hour_sin", "hour_cos", "year_sin", "year_cos")


def make_features(data: pd.DataFrame, use_environment: bool) -> pd.DataFrame:
    dt = pd.to_datetime(data["time"], utc=True)
    hour = dt.dt.hour + dt.dt.minute / 60
    day = dt.dt.dayofyear
    features = pd.DataFrame({
        "latitude": data["latitude"].to_numpy(dtype=float),
        "longitude": data["longitude"].to_numpy(dtype=float),
        "hour_sin": np.sin(2 * np.pi * hour / 24),
        "hour_cos": np.cos(2 * np.pi * hour / 24),
        "year_sin": np.sin(2 * np.pi * day / 365.25),
        "year_cos": np.cos(2 * np.pi * day / 365.25),
    }, index=data.index)
    if use_environment:
        absent = set(ENVIRONMENT_FEATURES) - set(data.columns)
        if absent:
            raise ValueError(f"Missing environmental features: {sorted(absent)}")
        for column in ENVIRONMENT_FEATURES:
            features[column] = pd.to_numeric(data[column], errors="raise")
        if not np.isfinite(features[list(ENVIRONMENT_FEATURES)].to_numpy()).all():
            raise ValueError("Environmental values contain missing/invalid entries")
    return features
