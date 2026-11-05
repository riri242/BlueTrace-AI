import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.features import make_features
from bluetrace_ml.physics import constant_current_backtrack


def test_inference_input_excludes_historical_targets_and_drifter_velocities():
    data = pd.DataFrame({
        "ID": [123],
        "time": [pd.Timestamp("2011-03-25T12:00:00Z")],
        "latitude": [36.8],
        "longitude": [-122.0],
        "previous_latitude": [36.7],
        "previous_longitude": [-121.8],
        "ve": [10.0],
        "vn": [9.0],
    })
    features = make_features(data, use_environment=False)
    assert not {"ID", "ve", "vn", "previous_latitude", "previous_longitude"} & set(features)


def test_no_weather_is_synthesized_at_inference():
    frame = pd.DataFrame({
        "time": [pd.Timestamp("2011-03-25T12:00:00Z")],
        "latitude": [36.8],
        "longitude": [-122.0],
    })
    with pytest.raises(ValueError, match="Missing environmental"):
        make_features(frame, use_environment=True)
    with pytest.raises(ValueError, match="Current components"):
        constant_current_backtrack(frame)
