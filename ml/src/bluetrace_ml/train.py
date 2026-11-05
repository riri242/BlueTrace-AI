"""Train an inference-safe location-only prototype or an environmental model.

The location-only model is a sanity-check baseline, not a validated physical origin model.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.dummy import DummyRegressor
from xgboost import XGBRegressor

from .dataset import make_24h_pairs, read_noaa
from .evaluate import score
from .features import make_features
from .splits import grouped_indices
from .physics import constant_current_backtrack


def run(noaa_csv: str, output_dir: str, config_file: str,
        environment_csv: str | None = None):
    config = json.loads(Path(config_file).read_text(encoding="utf-8"))
    hours = config.get("horizon_hours", 24)
    if hours != 24:
        raise ValueError("This initial experiment only supports a 24-hour horizon")
    data = make_24h_pairs(read_noaa(noaa_csv), hours=hours)
    if environment_csv:
        from .environment import join_environment
        data, coverage = join_environment(data, environment_csv)
    else:
        coverage = None
    use_environment = environment_csv is not None
    features = make_features(data, use_environment)
    targets = data[["target_east_km", "target_north_km"]].to_numpy(dtype=float)
    physical_offsets = constant_current_backtrack(data, hours) if use_environment else np.zeros_like(targets)
    regression_target = targets - physical_offsets
    splits = grouped_indices(data, seed=config["seed"],
                             test_fraction=config["test_fraction"],
                             validation_fraction=config["validation_fraction"])
    model = XGBRegressor(random_state=config["seed"], objective="reg:squarederror",
                         **config["xgboost"])
    model.fit(features.iloc[splits["train"]], regression_target[splits["train"]],
              eval_set=[(features.iloc[splits["validation"]], regression_target[splits["validation"]])],
              verbose=False)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    report = {
        "model": "hybrid_fixed_current_plus_xgboost_residual" if use_environment else "xgboost_multioutput_24h_offset",
        "mode": "hybrid_environmental_experimental" if use_environment else "location_only_experimental",
        "production_ready": False,
        "environment_coverage": coverage,
        "rows": int(len(data)),
        "unique_drifters": int(data["ID"].nunique()),
        "features": list(features.columns),
        "partitions": {},
        "metrics": {},
    }
    for name, indices in splits.items():
        subset = data.iloc[indices]
        report["partitions"][name] = {
            "rows": int(len(indices)),
            "drifters": sorted(str(v) for v in subset["ID"].unique()),
        }
        observed = model.predict(features.iloc[indices]) + physical_offsets[indices]
        report["metrics"][name] = {
            "xgboost": score(subset, observed),
            "no_movement": score(subset, np.zeros((len(indices), 2))),
        }
        if use_environment:
            report["metrics"][name]["constant_current"] = score(subset, physical_offsets[indices])
        if name == "test":
            dummy = DummyRegressor(strategy="mean")
            dummy.fit(features.iloc[splits["train"]], targets[splits["train"]])
            report["metrics"][name]["mean_displacement"] = score(
                subset, dummy.predict(features.iloc[indices])
            )
    joblib.dump({"model": model, "feature_names": list(features.columns),
                 "mode": report["mode"], "horizon_hours": hours}, out / "model.joblib")
    (out / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": "complete", "mode": report["mode"],
                      "test_metrics": report["metrics"]["test"],
                      "output": str(out)}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--noaa", required=True, help="NOAA hourly drifter CSV (including units row)")
    parser.add_argument("--environment", help="UTC-aligned environment CSV; see ml/README.md")
    parser.add_argument("--config", default="configs/experiment.json")
    parser.add_argument("--output", default="artifacts/prototype")
    args = parser.parse_args()
    run(args.noaa, args.output, args.config, args.environment)


if __name__ == "__main__":
    main()
