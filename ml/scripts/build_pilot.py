"""Build a small NOAA-aligned environmental training pilot.

From ml/:
  python scripts/build_pilot.py --noaa data/raw/drifter_hourly_qc.csv

This downloads small Copernicus subsets and hourly ERA5 wind records at
sampled observation locations. It does not download the entire study period.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from bluetrace_ml.dataset import make_24h_pairs, read_noaa

PRODUCTS = {
    "currents": {
        "dataset_id": "cmems_mod_glo_phy_my_0.083deg_P1D-m",
        "variables": ["uo", "vo"],
    },
    "waves": {
        "dataset_id": "cmems_mod_glo_wav_my_0.2deg_PT3H-i",
        "variables": ["VSDX", "VSDY", "VHM0"],
    },
}
ERA5_URL = "https://archive-api.open-meteo.com/v1/archive"


def select_observations(pairs: pd.DataFrame, sample_size: int, year: int, days: int):
    candidates = pairs.loc[pairs["time"].dt.year.eq(year)].copy()
    if candidates.empty:
        raise ValueError(f"No valid 24-hour NOAA pairs for {year}; select another --year")
    candidates["window"] = candidates["time"].dt.floor("D") - pd.to_timedelta(
        (candidates["time"].dt.dayofyear - 1) % days, unit="D"
    )
    counts = candidates.groupby("window").agg(
        n=("ID", "size"), drifters=("ID", "nunique"),
        lat_span=("latitude", lambda s: s.max() - s.min()),
        lon_span=("longitude", lambda s: s.max() - s.min()),
    )
    feasible = counts.loc[(counts["lat_span"] <= 2) & (counts["lon_span"] <= 2)]
    if feasible.empty:
        raise ValueError("No compact pilot window found; use another year or smaller study region")
    window = feasible.sort_values(["drifters", "n"], ascending=False).index[0]
    selected = candidates.loc[candidates["window"].eq(window)].copy()
    # Sample round-robin by drifter to prevent one trajectory dominating.
    selected = selected.sort_values(["ID", "time"])
    selected["rank"] = selected.groupby("ID").cumcount()
    selected = selected.sort_values(["rank", "ID"]).head(sample_size)
    return selected.drop(columns=["window", "rank"]).sort_values("time").reset_index(drop=True)


def subset_marine(frame: pd.DataFrame, directory: Path):
    try:
        import copernicusmarine
    except ImportError as exc:
        raise RuntimeError('Install Copernicus extras with pip install -e ".[dev,marine]"') from exc
    directory.mkdir(parents=True, exist_ok=True)
    output = {}
    begin = (frame["time"].min() - pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    end = (frame["time"].max() + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    for name, product in PRODUCTS.items():
        filename = f"{name}_pilot.nc"
        kwargs = {
            "dataset_id": product["dataset_id"],
            "variables": product["variables"],
            "minimum_latitude": float(frame["latitude"].min() - 0.4),
            "maximum_latitude": float(frame["latitude"].max() + 0.4),
            "minimum_longitude": float(frame["longitude"].min() - 0.4),
            "maximum_longitude": float(frame["longitude"].max() + 0.4),
            "start_datetime": begin,
            "end_datetime": end,
            "output_directory": str(directory),
            "output_filename": filename,
            "overwrite": True,
        }
        if name == "currents":
            kwargs.update(minimum_depth=0, maximum_depth=1)
        print(f"Downloading {name} ({begin} through {end})...")
        copernicusmarine.subset(**kwargs)
        output[name] = directory / filename
    return output


def sample_grid(path: Path, frame: pd.DataFrame, variables: list[str], tolerance_hours: int):
    import xarray as xr
    records = []
    with xr.open_dataset(path) as data:
        for row in frame.itertuples(index=False):
            point = data.sel(
                latitude=float(row.latitude),
                longitude=float(row.longitude),
                time=np.datetime64(row.time.tz_convert(None), "ns"),
                method="nearest",
            )
            source_time = pd.Timestamp(point["time"].item()).tz_localize("UTC")
            offset = abs((source_time - row.time).total_seconds()) / 3600
            values = {}
            for var in variables:
                try:
                    values[var] = float(point[var].isel(depth=0).item()) if "depth" in point[var].dims else float(point[var].item())
                except (ValueError, KeyError, IndexError):
                    values[var] = float("nan")
            records.append({
                **values,
                "source_time": source_time.isoformat(),
                "offset_hours": offset,
                "valid": offset <= tolerance_hours and all(math.isfinite(v) for v in values.values()),
                "grid_latitude": float(point.latitude.item()),
                "grid_longitude": float(point.longitude.item()),
            })
    return pd.DataFrame(records)


def sample_era5(frame: pd.DataFrame):
    session = requests.Session()
    records = []
    for index, row in enumerate(frame.itertuples(index=False), start=1):
        day = row.time.strftime("%Y-%m-%d")
        response = session.get(
            ERA5_URL,
            params={
                "latitude": round(float(row.latitude), 4),
                "longitude": round(float(row.longitude), 4),
                "start_date": day,
                "end_date": day,
                "hourly": "wind_speed_10m,wind_direction_10m",
                "wind_speed_unit": "ms",
                "timezone": "GMT",
                "models": "era5",
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"ERA5 request failed: {payload.get('reason', 'unknown')}")
        hourly = payload["hourly"]
        times = pd.to_datetime(hourly["time"], utc=True)
        target = row.time.floor("h")
        matching = np.flatnonzero(times == target)
        if not len(matching):
            records.append({"wind_u": np.nan, "wind_v": np.nan, "wind_source_time": None})
            continue
        j = int(matching[0])
        speed = hourly["wind_speed_10m"][j]
        direction = hourly["wind_direction_10m"][j]
        if speed is None or direction is None:
            u, v = np.nan, np.nan
        else:
            radians = np.radians(float(direction))
            u = -float(speed) * np.sin(radians)
            v = -float(speed) * np.cos(radians)
        records.append({"wind_u": u, "wind_v": v, "wind_source_time": times[j].isoformat()})
        print(f"ERA5 wind {index}/{len(frame)}", end="\r", flush=True)
    print()
    return pd.DataFrame(records)


def build(noaa: str, output: str, year: int, days: int, sample_size: int):
    if not 1 <= sample_size <= 100:
        raise ValueError("Pilot size must be between 1 and 100 observations")
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    pairs = make_24h_pairs(read_noaa(noaa))
    sample = select_observations(pairs, sample_size, year, days)
    if sample.empty:
        raise ValueError("No valid pilot observations")
    sample[["ID", "time", "latitude", "longitude"]].to_csv(output_dir / "pilot_noaa_observations.csv", index=False)
    marine = subset_marine(sample, output_dir / "marine")
    current = sample_grid(marine["currents"], sample, PRODUCTS["currents"]["variables"], tolerance_hours=24)
    waves = sample_grid(marine["waves"], sample, PRODUCTS["waves"]["variables"], tolerance_hours=2)
    wind = sample_era5(sample)
    result = sample[["ID", "time", "latitude", "longitude"]].copy()
    result["sample_latitude"] = result["latitude"]
    result["sample_longitude"] = result["longitude"]
    for col, val in {
        "current_u": current["uo"], "current_v": current["vo"],
        "stokes_u": waves["VSDX"], "stokes_v": waves["VSDY"],
        "wave_height": waves["VHM0"],
        "wind_u": wind["wind_u"], "wind_v": wind["wind_v"],
        "current_source_time": current["source_time"],
        "wave_source_time": waves["source_time"],
        "wind_source_time": wind["wind_source_time"],
        "current_offset_hours": current["offset_hours"],
        "wave_offset_hours": waves["offset_hours"],
        "current_grid_lat": current["grid_latitude"],
        "current_grid_lon": current["grid_longitude"],
        "wave_grid_lat": waves["grid_latitude"],
        "wave_grid_lon": waves["grid_longitude"],
    }.items():
        result[col] = val.to_numpy()
    required = ["wind_u", "wind_v", "current_u", "current_v", "stokes_u", "stokes_v"]
    all_valid = np.isfinite(result[required].to_numpy(dtype=float)).all(axis=1)
    all_valid &= current["valid"].to_numpy() & waves["valid"].to_numpy()
    result["complete_environment"] = all_valid
    result.to_csv(output_dir / "environment_pilot.csv", index=False)
    report = {
        "year": year,
        "noaa_observations": len(sample),
        "unique_drifters": int(sample["ID"].nunique()),
        "time_start_utc": sample["time"].min().isoformat(),
        "time_end_utc": sample["time"].max().isoformat(),
        "valid_current_rows": int(current["valid"].sum()),
        "valid_wave_rows": int(waves["valid"].sum()),
        "valid_wind_rows": int(np.isfinite(wind[["wind_u", "wind_v"]]).all(axis=1).sum()),
        "all_sources_complete_rows": int(all_valid.sum()),
        "all_sources_complete_fraction": float(all_valid.mean()),
        "training_ready": False,
        "note": "Small availability pilot only. No full-period integration or model-quality claim.",
    }
    (output_dir / "coverage_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--noaa", default="data/raw/drifter_hourly_qc.csv")
    p.add_argument("--output", default="data/interim/pilot")
    p.add_argument("--year", type=int, default=2011)
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--sample-size", type=int, default=24)
    a = p.parse_args()
    build(a.noaa, a.output, a.year, a.days, a.sample_size)
