"""Evaluate a small spatially evolving 24-hour marine backtrace pilot.

Run from ml/:
    python scripts/trace_trajectory.py --max-observations 3

Only reads cached Copernicus .nc files and the local NOAA CSV.
It never requests Copernicus credentials or downloads new marine data.
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import xarray as xr

from bluetrace_ml.dataset import make_24h_pairs, read_noaa, haversine_km
from bluetrace_ml.trajectory import MarineGrid, backtrack, score_trace

if __package__:
    from .build_temporal import cached_observations
else:
    from build_temporal import cached_observations


def run(*, noaa, root, output, max_observations=3, max_distance_degrees=0.4):
    if not 1 <= max_observations <= 12:
        raise ValueError("--max-observations must be in the range 1..12")
    selections = cached_observations(root, max_observations)
    if not selections:
        raise ValueError("No cached drifter observations found")

    pairs = make_24h_pairs(read_noaa(noaa))
    labels = pairs[["ID", "time", "previous_latitude", "previous_longitude"]].copy()
    labels["ID"] = labels["ID"].astype(str)
    index = labels.set_index(["ID", "time"], verify_integrity=True)

    rows = []
    paths = []
    for i, observation in enumerate(selections, 1):
        key = (str(observation["ID"]), pd.Timestamp(observation["time"]).tz_convert("UTC"))
        if key not in index.index:
            raise ValueError(f"Missing 24h NOAA truth for observation {key}")
        truth = index.loc[key]
        directory = observation["folder"] / "marine"
        with (xr.open_dataset(directory / "currents_pilot.nc") as currents,
              xr.open_dataset(directory / "waves_pilot.nc") as waves):
            grid = MarineGrid(
                currents, waves, max_distance_degrees=max_distance_degrees,
            )
            trace_current = backtrack(
                observation["latitude"], observation["longitude"],
                observation["time"], grid, include_stokes=False,
            )
            trace_stokes = backtrack(
                observation["latitude"], observation["longitude"],
                observation["time"], grid, include_stokes=True,
            )

        error_current = score_trace(
            trace_current, truth["previous_latitude"], truth["previous_longitude"]
        )
        error_stokes = score_trace(
            trace_stokes, truth["previous_latitude"], truth["previous_longitude"]
        )
        error_stationary = float(haversine_km(
            observation["latitude"], observation["longitude"],
            truth["previous_latitude"], truth["previous_longitude"],
        ))
        rows.append({
            "ID": str(observation["ID"]),
            "time": pd.Timestamp(observation["time"]).isoformat(),
            "current_steps": trace_current.steps,
            "current_status": trace_current.status,
            "current_reason": trace_current.reason,
            "current_error_km": error_current,
            "current_plus_stokes_steps": trace_stokes.steps,
            "current_plus_stokes_status": trace_stokes.status,
            "current_plus_stokes_reason": trace_stokes.reason,
            "current_plus_stokes_error_km": error_stokes,
            "no_movement_error_km": error_stationary,
        })
        paths.append({
            "ID": str(observation["ID"]),
            "observation_time": pd.Timestamp(observation["time"]).isoformat(),
            "current_only": list(trace_current.path),
            "current_plus_stokes": list(trace_stokes.path),
        })
        print(
            f"Observation {i}/{len(selections)}: "
            f"current={trace_current.steps}/24, "
            f"current+Stokes={trace_stokes.steps}/24"
        )

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame(rows)
    result.to_csv(output_dir / "comparison.csv", index=False)
    (output_dir / "paths.json").write_text(
        json.dumps(paths, indent=2), encoding="utf-8",
    )
    common = result.loc[result["current_error_km"].notna() & result["current_plus_stokes_error_km"].notna()]
    report = {
        "observations": len(rows),
        "common_completed_observations": int(len(common)),
        "common_subset_mean_current_only_error_km": float(common["current_error_km"].mean()) if len(common) else None,
        "common_subset_mean_current_plus_stokes_error_km": float(common["current_plus_stokes_error_km"].mean()) if len(common) else None,
        "common_subset_mean_no_movement_error_km": float(common["no_movement_error_km"].mean()) if len(common) else None,
        "completed_current_only": int(result["current_status"].eq("complete").sum()),
        "completed_current_plus_stokes": int(result["current_plus_stokes_status"].eq("complete").sum()),
        "mean_current_only_error_km": (
            float(result["current_error_km"].mean())
            if result["current_error_km"].notna().any() else None
        ),
        "mean_current_plus_stokes_error_km": (
            float(result["current_plus_stokes_error_km"].mean())
            if result["current_plus_stokes_error_km"].notna().any() else None
        ),
        "mean_no_movement_error_km": float(result["no_movement_error_km"].mean()),
        "production_ready": False,
        "limitations": [
            "Retrospective Copernicus grids are not operational availability guarantees.",
            "Daily averaged currents can incorporate measurements later in the labeled calendar day.",
            "Nearest-grid backward Euler; no coast collision, beaching or interpolation.",
            "Stokes drift addition is exploratory and not calibrated for actual NOAA drifter coupling.",
            "Windage is not included in this CLI experiment.",
            "Compare methods on the exact common completed subset before drawing conclusions.",
        ],
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--noaa", default="data/raw/drifter_hourly_qc.csv")
    p.add_argument("--root", default="data/interim/diverse")
    p.add_argument("--output", default="data/interim/trajectory_pilot")
    p.add_argument("--max-observations", type=int, default=3)
    p.add_argument("--max-distance-degrees", type=float, default=0.4)
    args = p.parse_args()
    run(noaa=args.noaa, root=args.root, output=args.output,
        max_observations=args.max_observations,
        max_distance_degrees=args.max_distance_degrees)


if __name__ == "__main__":
    main()
