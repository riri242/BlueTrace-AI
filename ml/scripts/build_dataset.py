"""Build a reproducible, bounded multi-year environmental coverage dataset.

Run from ml/:
    python scripts/build_dataset.py --years 2005 2011 2018 --sample-size 24

Each year is an independent NOAA/Copernicus/ERA5 pilot. Successful batches
are resumable by selection fingerprint; failed batches can be retried.
This is a coverage and model-feasibility study, not a full ocean hindcast.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bluetrace_ml.dataset import make_24h_pairs, read_noaa
from bluetrace_ml.features import ENVIRONMENT_FEATURES
from build_pilot import select_observations, subset_marine, sample_grid, sample_era5, PRODUCTS


def fingerprint(frame):
    canonical = frame[["ID", "time", "latitude", "longitude"]].copy()
    canonical["time"] = pd.to_datetime(canonical["time"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return hashlib.sha256(canonical.to_csv(index=False).encode("utf-8")).hexdigest()


def run_batch(frame, out_dir, *, reuse=True):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    signature = fingerprint(frame)
    manifest_path = out_dir / "manifest.json"
    csv_path = out_dir / "environment.csv"

    if reuse and manifest_path.is_file() and csv_path.is_file():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("selection_sha256") == signature and old.get("state") == "complete":
            cached = pd.read_csv(csv_path)
            if len(cached) == len(frame):
                print(f"Reusing completed batch: {out_dir}")
                return cached, old

    marine = subset_marine(frame, out_dir / "marine")
    currents = sample_grid(marine["currents"], frame, PRODUCTS["currents"]["variables"], tolerance_hours=24)
    waves = sample_grid(marine["waves"], frame, PRODUCTS["waves"]["variables"], tolerance_hours=2)
    winds = sample_era5(frame)
    result = frame[["ID", "time", "latitude", "longitude"]].copy().reset_index(drop=True)
    result["sample_latitude"] = result["latitude"]
    result["sample_longitude"] = result["longitude"]
    fields = {
        "current_u": currents["uo"], "current_v": currents["vo"],
        "stokes_u": waves["VSDX"], "stokes_v": waves["VSDY"],
        "wave_height": waves["VHM0"],
        "wind_u": winds["wind_u"], "wind_v": winds["wind_v"],
        "current_source_time": currents["source_time"],
        "wave_source_time": waves["source_time"],
        "wind_source_time": winds["wind_source_time"],
        "current_offset_hours": currents["offset_hours"],
        "wave_offset_hours": waves["offset_hours"],
        "current_grid_lat": currents["grid_latitude"],
        "current_grid_lon": currents["grid_longitude"],
        "wave_grid_lat": waves["grid_latitude"],
        "wave_grid_lon": waves["grid_longitude"],
    }
    for field, values in fields.items():
        result[field] = values.to_numpy()
    finite = np.isfinite(result[list(ENVIRONMENT_FEATURES)].to_numpy(dtype=float)).all(axis=1)
    valid = finite & currents["valid"].to_numpy() & waves["valid"].to_numpy()
    result["complete_environment"] = valid
    manifest = {
        "state": "complete",
        "selection_sha256": signature,
        "count": len(frame),
        "drifters": int(frame["ID"].nunique()),
        "start_utc": str(frame["time"].min()),
        "end_utc": str(frame["time"].max()),
        "valid_current_rows": int(currents["valid"].sum()),
        "valid_wave_rows": int(waves["valid"].sum()),
        "valid_wind_rows": int(np.isfinite(winds[["wind_u", "wind_v"]].to_numpy()).all(axis=1).sum()),
        "complete_rows": int(valid.sum()),
        "current_product": PRODUCTS["currents"]["dataset_id"],
        "wave_product": PRODUCTS["waves"]["dataset_id"],
        "wind_product": "Open-Meteo ERA5 archive",
        "source_matching": "nearest sea grid (current max 24h, wave max 2h), hourly UTC wind",
        "training_ready": False,
    }
    result.to_csv(csv_path, index=False)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return result, manifest


def build(noaa, years, sample_size, out_dir, *, reuse=True):
    if not years or len(set(years)) != len(years):
        raise ValueError("Select one or more distinct years")
    if not 1 <= sample_size <= 100:
        raise ValueError("--sample-size must be 1..100")
    out_dir = Path(out_dir)
    pairs = make_24h_pairs(read_noaa(noaa))
    batches = []
    manifests = []
    for year in years:
        chosen = select_observations(pairs, sample_size, year, 3)
        output, info = run_batch(chosen, out_dir / "batches" / str(year), reuse=reuse)
        batches.append(output)
        manifests.append({"year": year, **info})
        print(f"Year {year}: {info['complete_rows']}/{info['count']} complete")
    merged = pd.concat(batches, ignore_index=True)
    if merged.duplicated(["ID", "time"]).any():
        raise ValueError("Duplicate NOAA ID/time after batch merge")
    joined = merged.loc[merged["complete_environment"].astype(str).str.lower() == "true"].copy()
    # Training accepts only the strict feature schema and valid sampled locations.
    features = ["ID", "time", "sample_latitude", "sample_longitude", *ENVIRONMENT_FEATURES]
    out_dir.mkdir(parents=True, exist_ok=True)
    joined[features].to_csv(out_dir / "environment.csv", index=False)
    report = {
        "years": years,
        "selected_rows": int(len(merged)),
        "complete_rows": int(len(joined)),
        "complete_fraction": float(len(joined) / len(merged)),
        "unique_drifters": int(joined["ID"].nunique()),
        "valid_current_rows": int(sum(m["valid_current_rows"] for m in manifests)),
        "valid_wave_rows": int(sum(m["valid_wave_rows"] for m in manifests)),
        "valid_wind_rows": int(sum(m["valid_wind_rows"] for m in manifests)),
        "batches": manifests,
        "training_ready": False,
        "reason": "This is a bounded snapshot pilot. It is not a validated 24-hour environmental integration or an independent multi-year model benchmark.",
        "environment_csv": str(out_dir / "environment.csv"),
    }
    (out_dir / "coverage_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "batches"}, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--noaa", default="data/raw/drifter_hourly_qc.csv")
    p.add_argument("--years", nargs="+", type=int, default=[2005, 2011, 2018])
    p.add_argument("--sample-size", type=int, default=24)
    p.add_argument("--output", default="data/interim/multiyear")
    p.add_argument("--refresh", action="store_true", help="Re-download and validate batches even if cached")
    args = p.parse_args()
    build(args.noaa, args.years, args.sample_size, args.output, reuse=not args.refresh)


if __name__ == "__main__":
    main()
