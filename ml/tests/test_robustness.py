"""Offline checks for grouped repeated-evaluation safeguards."""
import numpy as np
import pandas as pd
import pytest

from bluetrace_ml.robustness import summarize, year_holdout_splits, evaluate_partition


def frame():
    rows = []
    for year in (2010, 2011, 2015):
        for drifter in range(5):
            rows.append({
                "ID": f"{year}-{drifter}",
                "time": pd.Timestamp(year=year, month=1, day=1, tz="UTC"),
                "latitude": 36.0 + drifter * 0.1,
                "longitude": -122.0,
                "previous_latitude": 36.0 + drifter * 0.1,
                "previous_longitude": -122.0,
            })
    return pd.DataFrame(rows)


def test_year_holdout_excludes_shared_drifters():
    sample = frame()
    groups = sample["ID"].to_numpy()
    folds = list(year_holdout_splits(sample, validation_fraction=0.2))
    assert len(folds) == 3
    for year, train, validation, test in folds:
        assert sample.iloc[test]["time"].dt.year.eq(year).all()
        assert not (set(groups[train]) & set(groups[test]))
        assert not (set(groups[validation]) & set(groups[test]))
        assert not (set(groups[validation]) & set(groups[train]))


def test_evaluate_partition_rejects_shared_drifter():
    data = frame()
    features = pd.DataFrame({"x": np.zeros(len(data))})
    targets = np.zeros((len(data), 2))
    with pytest.raises(ValueError, match="shared drifter"):
        evaluate_partition(
            data, features, targets, targets,
            np.array([0, 1]), np.array([2]), np.array([0]),
            {"xgboost": {"n_estimators": 2}}, 42, "leaking",
        )


def test_summary_counts_wins():
    def result(hybrid, current):
        return {
            "metrics": {
                "hybrid": {"mean_error_km": hybrid},
                "constant_current": {"mean_error_km": current},
                "no_movement": {"mean_error_km": 20.0},
            },
            "improvement_mean_error_percent_vs_current": (current - hybrid) / current * 100,
        }
    summary = summarize([result(5.0, 10.0), result(15.0, 10.0)])
    assert summary["folds"] == 2
    assert summary["hybrid_beats_current_in_folds"] == 1
    assert summary["hybrid"]["mean_of_test_mean_errors_km"] == 10.0
