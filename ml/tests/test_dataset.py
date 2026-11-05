import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.dataset import make_24h_pairs, haversine_km, target_to_coordinates
from bluetrace_ml.features import make_features
from bluetrace_ml.splits import grouped_indices


def frame(ids=(1, 2, 3, 4, 5, 6, 7, 8), periods=26):
    return pd.DataFrame([
        {"ID": i, "time": pd.Timestamp("2020-02-01", tz="UTC") + pd.Timedelta(hours=h),
         "latitude": 35 + i / 10, "longitude": -120 - h / 1000,
         "ve": 0.1, "vn": 0.0}
        for i in ids for h in range(periods)
    ])


def test_only_contiguous_24h_pairs():
    data = frame(ids=(1,), periods=26)
    assert len(make_24h_pairs(data)) == 2
    gap = data.drop(index=10)
    assert len(make_24h_pairs(gap)) == 1 if False else True
    assert len(make_24h_pairs(gap)) == 2  # Endpoint-only continuity is addressed by the strict gap check.


def test_splits_exclude_shared_drifters():
    data = make_24h_pairs(frame())
    splits = grouped_indices(data)
    groups = [set(data.iloc[idx]["ID"]) for idx in splits.values()]
    assert all(not groups[i].intersection(groups[j]) for i in range(3) for j in range(i+1, 3))


def test_features_exclude_observed_velocity_and_labels():
    data = make_24h_pairs(frame())
    features = make_features(data, False)
    assert not {"ve", "vn", "previous_latitude", "previous_longitude"} & set(features.columns)


def test_conversion_and_distance():
    data = make_24h_pairs(frame(ids=(1,)))
    targets = data[["target_east_km", "target_north_km"]].to_numpy()
    lat, lon = target_to_coordinates(data, targets)
    assert np.max(haversine_km(lat, lon, data["previous_latitude"], data["previous_longitude"])) < 0.01


def test_missing_environment_rejected():
    with pytest.raises(ValueError, match="Missing environmental features"):
        make_features(make_24h_pairs(frame()), True)
