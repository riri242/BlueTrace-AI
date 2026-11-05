import json

import pandas as pd

from bluetrace_ml.train import run


def test_training_outputs_group_heldout_metrics(tmp_path):
    rows = []
    for drifter in range(1, 11):
        for hour in range(27):
            rows.append({
                "ID": drifter,
                "time": (pd.Timestamp("2011-03-25T00:00:00Z") +
                         pd.Timedelta(hours=hour)).isoformat(),
                "latitude": 34 + drifter / 3 + hour * 0.0001,
                "longitude": -121 - drifter / 10 + hour * 0.001,
                "ve": 0.1,
                "vn": 0.01,
            })
    csv = tmp_path / "noaa.csv"
    pd.DataFrame(rows).to_csv(csv, index=False)
    config = {
        "seed": 42,
        "horizon_hours": 24,
        "test_fraction": 0.2,
        "validation_fraction": 0.2,
        "xgboost": {
            "n_estimators": 6,
            "max_depth": 2,
            "learning_rate": 0.1,
            "n_jobs": 1,
        },
    }
    file = tmp_path / "experiment.json"
    file.write_text(json.dumps(config), encoding="utf-8")
    results = run(str(csv), str(tmp_path / "artifacts"), str(file))
    assert not results["production_ready"]
    assert results["mode"] == "location_only_experimental"
    assert results["metrics"]["test"]["no_movement"]["count"] > 0
    ids = [set(part["drifters"]) for part in results["partitions"].values()]
    assert all(not ids[i] & ids[j] for i in range(3) for j in range(i + 1, 3))
    assert (tmp_path / "artifacts" / "model.joblib").is_file()
    assert (tmp_path / "artifacts" / "evaluation.json").is_file()
