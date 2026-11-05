"""Offline inference from a trusted, locally trained artifact.

Prediction inputs must match features present during training. This module
does not substitute live Open-Meteo values for unavailable historical inputs.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .dataset import target_to_coordinates
from .features import make_features
from .physics import constant_current_backtrack


def predict_previous_position(artifact: str | Path, observations: pd.DataFrame):
    saved = joblib.load(artifact)
    model = saved["model"]
    use_environment = saved["mode"] == "hybrid_environmental_experimental"
    features = make_features(observations, use_environment=use_environment)
    if list(features.columns) != list(saved["feature_names"]):
        raise ValueError("Inference feature schema does not match trained artifact")
    offsets = model.predict(features)
    if use_environment:
        offsets += constant_current_backtrack(observations, saved["horizon_hours"])
    lat, lon = target_to_coordinates(observations, np.asarray(offsets))
    return pd.DataFrame({
        "predicted_previous_latitude": lat,
        "predicted_previous_longitude": lon,
    }, index=observations.index)
