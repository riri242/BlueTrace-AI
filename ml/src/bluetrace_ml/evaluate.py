"""Geodesic backtracking error metrics."""

import numpy as np

from .dataset import haversine_km, target_to_coordinates


def score(frame, offsets):
    lat_pred, lon_pred = target_to_coordinates(frame, np.asarray(offsets, dtype=float))
    errors = haversine_km(frame["previous_latitude"], frame["previous_longitude"],
                          lat_pred, lon_pred)
    if not len(errors):
        raise ValueError("Cannot evaluate an empty dataset")
    return {
        "count": int(len(errors)),
        "mean_error_km": float(np.mean(errors)),
        "median_error_km": float(np.median(errors)),
        "p90_error_km": float(np.percentile(errors, 90)),
        "max_error_km": float(np.max(errors)),
    }
