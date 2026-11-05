"""Select diverse NOAA observations across compact space-time batches.

Preview first (no network):
    python scripts/build_diverse.py --years 2010 2011 2015 2021 2022
Download only after inspecting the selection report:
    python scripts/build_diverse.py --years 2010 2011 2015 2021 2022 --download

Each batch covers up to three days and a tight bounding box. Completed
batches are reused by NOAA selection fingerprint. This remains a bounded
snapshot-coverage experiment; it is not a validated debris-origin dataset.
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from bluetrace_ml.dataset import make_24h_pairs, read_noaa
if __package__:
    from .build_dataset import run_batch
else:
    from build_dataset import run_batch


def select_windows(pairs, years, *, windows_per_year=3, rows_per_window=12,
                   window_days=3, max_span=2.0):
    """Prioritize new drifter IDs, then distinct windows, within strict bounds."""
    if not years or len(set(years)) != len(years):
        raise ValueError("Years must be nonempty and distinct")
    if not 1 <= windows_per_year <= 12 or not 1 <= rows_per_window <= 100:
        raise ValueError("Invalid bounded sampling limits")
    if not 1 <= window_days <= 7 or not 0 < max_span <= 5:
        raise ValueError("Invalid temporal or spatial bounds")

    observations = pairs.loc[pairs["time"].dt.year.isin(years)].copy()
    observations["window"] = observations["time"].dt.floor("D") - pd.to_timedelta(
        (observations["time"].dt.dayofyear - 1) % window_days, unit="D"
    )
    observations = observations.sort_values(["time", "ID"])
    selected = []
    used_drifters = set()
    for year in years:
        subset = observations.loc[observations["time"].dt.year.eq(year)]
        if subset.empty:
            print(f"Year {year}: no eligible pairs, skipped")
            continue
        candidates = []
        for start, batch in subset.groupby("window", sort=True):
            # Reject windows whose extent would produce large Copernicus downloads.
            if (batch["latitude"].max() - batch["latitude"].min() > max_span
                    or batch["longitude"].max() - batch["longitude"].min() > max_span):
                # One window may have widely separated drifters. Partition by
                # independent spatial grid tiles instead of discarding it.
                batch = batch.copy()
                batch["tile_lat"] = (batch["latitude"] / max_span).floordiv(1).astype(int)
                batch["tile_lon"] = (batch["longitude"] / max_span).floordiv(1).astype(int)
                groups = [group for _, group in batch.groupby(["tile_lat", "tile_lon"])]
            else:
                groups = [batch]
            for tile_number, group in enumerate(groups):
                if group.empty:
                    continue
                distinct = group.drop_duplicates("ID")
                candidates.append((start, tile_number, group.copy(), set(distinct["ID"])))
        chosen = set()
        for _ in range(min(windows_per_year, len(candidates))):
            options = [
                (i, len(ids - used_drifters),
                 len(ids), len(group), -int(start.value))
                for i, (start, _, group, ids) in enumerate(candidates)
                if i not in chosen
            ]
            if not options:
                break
            best = max(options, key=lambda x: x[1:])
            idx = best[0]
            chosen.add(idx)
            start, tile_number, frame, _ = candidates[idx]
            # Start with one observation for each new drifter; then other
            # drifters. Fill the remaining quota with different times.
            frame = frame.copy().sort_values(["ID", "time"])
            frame["first_rank"] = frame.groupby("ID").cumcount()
            frame["unseen"] = (~frame["ID"].isin(used_drifters)).astype(int)
            frame = frame.sort_values(
                ["first_rank", "unseen", "ID", "time"],
                ascending=[True, False, True, True],
            ).head(rows_per_window)
            used_drifters.update(frame["ID"].unique())
            selected.append({
                "year": int(year),
                "window_start": start.strftime("%Y-%m-%d"),
                "tile": int(tile_number),
                "frame": frame.drop(columns=["window", "tile_lat", "tile_lon",
                                               "first_rank", "unseen"], errors="ignore")
                              .sort_values(["ID", "time"]).reset_index(drop=True),
            })
    return selected


def describe_selection(batches):
    if not batches:
        return {
            "selected_windows": 0, "selected_rows": 0, "unique_drifters": 0,
            "by_year": {}, "windows": [],
        }
    frames = [b["frame"] for b in batches]
    combined = pd.concat(frames, ignore_index=True)
    return {
        "selected_windows": len(batches),
        "selected_rows": len(combined),
        "unique_drifters": int(combined["ID"].nunique()),
        "by_year": {
            str(y): {
                "windows": sum(b["year"] == y for b in batches),
                "observations": sum(len(b["frame"]) for b in batches if b["year"] == y),
                "drifters": int(pd.concat(
                    [b["frame"] for b in batches if b["year"] == y]
                )["ID"].nunique()),
            }
            for y in sorted({b["year"] for b in batches})
        },
        "windows": [{
            "year": b["year"], "start_utc": b["window_start"],
            "tile": b["tile"], "rows": len(b["frame"]),
            "drifters": int(b["frame"]["ID"].nunique()),
            "latitude_span": float(b["frame"]["latitude"].max() - b["frame"]["latitude"].min()),
            "longitude_span": float(b["frame"]["longitude"].max() - b["frame"]["longitude"].min()),
        } for b in batches],
    }


def build(*, noaa, years, output, windows_per_year, rows_per_window, download=False):
    pairs = make_24h_pairs(read_noaa(noaa))
    batches = select_windows(pairs, years, windows_per_year=windows_per_year,
                             rows_per_window=rows_per_window)
    report = describe_selection(batches)
    out_dir = Path(output)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "selection_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items()
                      if key != "windows"}, indent=2))
    if not batches:
        raise ValueError("No eligible NOAA windows for the requested years")
    if not download:
        print("Preview only: no network downloads. Run with --download to fetch sources.")
        return report
    outputs = []
    complete = []
    for number, batch in enumerate(batches, start=1):
        key = f"{batch['year']}_{batch['window_start']}_tile{batch['tile']}"
        print(f"Batch {number}/{len(batches)}: {key}")
        try:
            data, manifest = run_batch(batch["frame"], out_dir / "batches" / key)
        except Exception:
            print(f"Batch {key} failed; already completed batches remain cached.")
            raise
        outputs.append(data)
        complete.append(manifest)
    combined = pd.concat(outputs, ignore_index=True)
    if combined.duplicated(["ID", "time"]).any():
        raise ValueError("Overlapping ID/timestamps across windows")
    valid = combined.loc[combined["complete_environment"].astype(str).str.lower().eq("true")]
    columns = [
        "ID", "time", "sample_latitude", "sample_longitude",
        "wind_u", "wind_v", "current_u", "current_v", "stokes_u", "stokes_v",
    ]
    valid[columns].to_csv(out_dir / "environment.csv", index=False)
    report["complete_rows"] = int(len(valid))
    report["complete_fraction"] = float(len(valid) / len(combined))
    report["complete_drifters"] = int(valid["ID"].nunique())
    report["training_ready"] = False
    report["reason"] = ("Snapshot coverage only; not a validated backtracking model "
                        "or full 24-hour environmental trajectory integration")
    (out_dir / "coverage_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "windows"}, indent=2))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--noaa", default="data/raw/drifter_hourly_qc.csv")
    p.add_argument("--years", type=int, nargs="+", default=[2010, 2011, 2015, 2021, 2022])
    p.add_argument("--windows-per-year", type=int, default=3)
    p.add_argument("--rows-per-window", type=int, default=12)
    p.add_argument("--output", default="data/interim/diverse")
    p.add_argument("--download", action="store_true")
    args = p.parse_args()
    build(noaa=args.noaa, years=args.years, output=args.output,
          windows_per_year=args.windows_per_year,
          rows_per_window=args.rows_per_window, download=args.download)


if __name__ == "__main__":
    main()
