import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.environment import join_environment
from bluetrace_ml.features import ENVIRONMENT_FEATURES


def paired_data():
    start = pd.Timestamp("2011-03-25T00:00:00Z")
    return pd.DataFrame([
        {"ID": identifier, "time": start,
         "latitude": 36.5 + identifier * 0.1, "longitude": -122.0,
         "previous_latitude": 36.4, "previous_longitude": -122.1,
         "target_east_km": -5.0, "target_north_km": -1.0}
        for identifier in range(1, 9)
    ])


def environment_data(pairs):
    frame = pairs[["ID", "time"]].copy()
    frame["sample_latitude"] = pairs["latitude"]
    frame["sample_longitude"] = pairs["longitude"]
    for variable in ENVIRONMENT_FEATURES:
        frame[variable] = 0.05
    return frame


def test_complete_environment_match(tmp_path):
    pairs = paired_data()
    path = tmp_path / "environment.csv"
    environment_data(pairs).to_csv(path, index=False)
    joined, report = join_environment(pairs, path)
    assert len(joined) == 8
    assert report["fraction"] == 1


def test_missing_currents_never_filled_with_zero(tmp_path):
    pairs = paired_data()
    env = environment_data(pairs)
    env["current_u"] = np.nan
    path = tmp_path / "environment.csv"
    env.to_csv(path, index=False)
    with pytest.raises(ValueError, match="No complete environment"):
        join_environment(pairs, path)


def test_duplicate_ids_and_times_rejected(tmp_path):
    pairs = paired_data()
    env = environment_data(pairs)
    path = tmp_path / "environment.csv"
    pd.concat([env, env.iloc[[0]]]).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Duplicate environment"):
        join_environment(pairs, path)


def test_rejects_spatially_mismatched_samples(tmp_path):
    pairs = paired_data()
    env = environment_data(pairs)
    env["sample_latitude"] += 2
    path = tmp_path / "environment.csv"
    env.to_csv(path, index=False)
    with pytest.raises(ValueError, match="No complete environment"):
        join_environment(pairs, path)
