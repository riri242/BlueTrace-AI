"""Group-disjoint repeated evaluation of experimental drifter backtracking.

Run from ml/:
  python -m bluetrace_ml.robustness --noaa data/raw/drifter_hourly_qc.csv \
      --environment data/interim/diverse/environment.csv \
      --output artifacts/hybrid_v2_evaluation

This module does not save or promote a fitted production model.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBRegressor

from .dataset import make_24h_pairs, read_noaa
from .environment import join_environment
from .evaluate import score
from .features import make_features
from .physics import constant_current_backtrack
from .splits import grouped_indices


def evaluate_partition(frame, features, targets, physics, train_idx, valid_idx,
                       test_idx, config, seed, label):
    groups = frame["ID"].astype(str).to_numpy()
    train_ids = set(groups[train_idx])
    valid_ids = set(groups[valid_idx])
    test_ids = set(groups[test_idx])
    if not train_ids or not valid_ids or not test_ids:
        raise ValueError(f"Empty data split for {label}")
    if train_ids & valid_ids or train_ids & test_ids or valid_ids & test_ids:
        raise ValueError(f"Data leakage: shared drifter ID across partitions in {label}")

    model = XGBRegressor(
        random_state=seed,
        objective="reg:squarederror",
        **config["xgboost"],
    )
    residual = targets - physics
    model.fit(
        features.iloc[train_idx],
        residual[train_idx],
        eval_set=[(features.iloc[valid_idx], residual[valid_idx])],
        verbose=False,
    )
    held_out = frame.iloc[test_idx]
    predictions = model.predict(features.iloc[test_idx]) + physics[test_idx]
    if predictions.shape != targets[test_idx].shape:
        raise ValueError(f"Unexpected model output shape in {label}")
    metrics = {
        "hybrid": score(held_out, predictions),
        "constant_current": score(held_out, physics[test_idx]),
        "no_movement": score(held_out, np.zeros_like(targets[test_idx])),
    }
    return {
        "name": label,
        "seed": int(seed),
        "split": {
            "train_rows": int(len(train_idx)),
            "validation_rows": int(len(valid_idx)),
            "test_rows": int(len(test_idx)),
            "train_drifters": len(train_ids),
            "validation_drifters": len(valid_ids),
            "test_drifters": len(test_ids),
        },
        "test_years": sorted(int(y) for y in frame.iloc[test_idx]["time"].dt.year.unique()),
        "metrics": metrics,
        "improvement_mean_error_percent_vs_current": float(
            100 * (metrics["constant_current"]["mean_error_km"] -
                   metrics["hybrid"]["mean_error_km"]) /
            metrics["constant_current"]["mean_error_km"]
        ) if metrics["constant_current"]["mean_error_km"] > 0 else None,
    }


def summarize(results):
    if not results:
        return {}
    improvements = [r["improvement_mean_error_percent_vs_current"]
                    for r in results if r["improvement_mean_error_percent_vs_current"] is not None]
    model_names = ("hybrid", "constant_current", "no_movement")
    result = {}
    for name in model_names:
        values = np.array([r["metrics"][name]["mean_error_km"] for r in results])
        result[name] = {
            "mean_of_test_mean_errors_km": float(values.mean()),
            "std_of_test_mean_errors_km": float(values.std(ddof=0)),
            "min_test_mean_error_km": float(values.min()),
            "max_test_mean_error_km": float(values.max()),
        }
    result["hybrid_beats_current_in_folds"] = sum(
        r["metrics"]["hybrid"]["mean_error_km"] <
        r["metrics"]["constant_current"]["mean_error_km"] for r in results
    )
    result["folds"] = len(results)
    result["improvement_vs_current_percent_median"] = (
        float(np.median(improvements)) if improvements else None
    )
    return result


def year_holdout_splits(frame, validation_fraction, seed=42):
    """Yield only year holdouts with disjoint drifters in all three sets."""
    groups = frame["ID"].astype(str).to_numpy()
    all_indices = np.arange(len(frame))
    for year in sorted(int(value) for value in frame["time"].dt.year.unique()):
        test = all_indices[frame["time"].dt.year.to_numpy() == year]
        test_ids = set(groups[test])
        # Prevent any trajectory crossing test-year boundary from training.
        trainval = all_indices[
            (frame["time"].dt.year.to_numpy() != year)
            & ~np.isin(groups, list(test_ids))
        ]
        if len(test_ids) < 2 or len(set(groups[trainval])) < 4:
            continue
        relative = GroupShuffleSplit(
            n_splits=1,
            test_size=validation_fraction,
            random_state=seed + year,
        )
        train_local, valid_local = next(
            relative.split(trainval, groups=groups[trainval])
        )
        train = trainval[train_local]
        valid = trainval[valid_local]
        if len(set(groups[train])) < 2 or len(set(groups[valid])) < 1:
            continue
        yield year, train, valid, test


def run(noaa, environment, output, config_file="configs/experiment.json", seeds=None):
    config = json.loads(Path(config_file).read_text(encoding="utf-8"))
    if int(config.get("horizon_hours", 24)) != 24:
        raise ValueError("Only the 24-hour horizon is supported")
    if seeds is None:
        seeds = [11, 23, 42, 71, 101]
    if len(seeds) < 2 or len(seeds) != len(set(seeds)):
        raise ValueError("At least two distinct seeds are required")
    frame = make_24h_pairs(read_noaa(noaa))
    frame, coverage = join_environment(frame, environment)
    features = make_features(frame, use_environment=True)
    targets = frame[["target_east_km", "target_north_km"]].to_numpy(dtype=float)
    physics = constant_current_backtrack(frame, hours=24)

    repeats = []
    for seed in seeds:
        partitions = grouped_indices(
            frame, seed=int(seed),
            test_fraction=config["test_fraction"],
            validation_fraction=config["validation_fraction"],
        )
        repeats.append(evaluate_partition(
            frame, features, targets, physics,
            partitions["train"], partitions["validation"],
            partitions["test"], config, int(seed), f"group_seed_{seed}",
        ))

    years = []
    for year, train, valid, test in year_holdout_splits(
        frame, config["validation_fraction"], seed=int(config["seed"])
    ):
        years.append(evaluate_partition(
            frame, features, targets, physics, train, valid, test,
            config, int(config["seed"]), f"held_out_year_{year}",
        ))

    result = {
        "status": "complete",
        "mode": "hybrid_robustness_experimental",
        "production_ready": False,
        "dataset_rows": int(len(frame)),
        "unique_drifters": int(frame["ID"].nunique()),
        "years": sorted(int(y) for y in frame["time"].dt.year.unique()),
        "environment_coverage": coverage,
        "group_repeats": repeats,
        "group_summary": summarize(repeats),
        "year_holdouts": years,
        "year_summary": summarize(years),
        "limitations": [
            "Only observation-time environmental snapshots, not 24-hour back-integrated conditions.",
            "NOAA drifters are not observed marine debris.",
            "Sparse observations per drifter and small held-out year groups make metrics uncertain.",
            "Repeated folds share observations; aggregate mean-of-fold metrics are not independent confidence intervals.",
        ],
    }
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out / "robustness.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "rows": result["dataset_rows"],
        "drifters": result["unique_drifters"],
        "group_summary": result["group_summary"],
        "year_summary": result["year_summary"],
        "year_holdout_folds": len(years),
        "output": str(out / "robustness.json"),
    }, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noaa", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--config", default="configs/experiment.json")
    parser.add_argument("--output", default="artifacts/hybrid_v2_evaluation")
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 23, 42, 71, 101])
    args = parser.parse_args()
    run(args.noaa, args.environment, args.output,
        config_file=args.config, seeds=args.seeds)


if __name__ == "__main__":
    main()
