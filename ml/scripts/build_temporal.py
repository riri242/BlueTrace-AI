"""Build a small 24-hour retrospective feature pilot from cached marine grids.

Run from ml/:
    python scripts/build_temporal.py --max-observations 3

Requires prior build_diverse.py --download. Never requests Copernicus again;
Open-Meteo historical archive is queried once per selected observation.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import xarray as xr

from bluetrace_ml.temporal import (
    CHANNELS, HOURS, backward_match, hourly_grid, summarize_history,
)

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def cached_observations(root, limit):
    batches = Path(root) / "batches"
    if not batches.exists():
        raise FileNotFoundError(f"No cached environmental batches: {batches}")
    selections = []
    seen = set()
    for folder in sorted(batches.iterdir()):
        manifest_path = folder / "manifest.json"
        source_csv = folder / "environment.csv"
        if not folder.is_dir() or not manifest_path.exists() or not source_csv.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("state") != "complete":
            continue
        frame = pd.read_csv(source_csv)
        for row in frame.itertuples(index=False):
            drifter = str(row.ID)
            if drifter in seen:
                continue
            if str(row.complete_environment).lower() != "true":
                continue
            if not (folder / "marine" / "currents_pilot.nc").exists():
                continue
            if not (folder / "marine" / "waves_pilot.nc").exists():
                continue
            selections.append({
                "ID": row.ID, "time": pd.Timestamp(row.time),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "folder": folder,
            })
            seen.add(drifter)
            if len(selections) >= limit:
                return selections
    return selections


def grid_history(path, location, times, columns, max_age_hours):
    fields = {}
    timestamps = {}
    with xr.open_dataset(path) as data:
        point = data.sel(
            latitude=float(location["latitude"]),
            longitude=float(location["longitude"]),
            method="nearest",
        )
        for output, source in columns.items():
            array = point[source]
            if "depth" in array.dims:
                array = array.isel(depth=0)
            source_time = pd.to_datetime(array["time"].values, utc=True)
            values = np.asarray(array.values, dtype=float).reshape(-1)
            fields[output], timestamps[output] = backward_match(
                source_time, values, times, max_age_hours,
            )
    return fields, timestamps


def wind_history(location, times, session):
    observation = times[-1]
    start = times[0].strftime("%Y-%m-%d")
    end = observation.strftime("%Y-%m-%d")
    response = session.get(ARCHIVE, params={
        "latitude": round(location["latitude"], 4),
        "longitude": round(location["longitude"], 4),
        "start_date": start,
        "end_date": end,
        "hourly": "wind_speed_10m,wind_direction_10m",
        "wind_speed_unit": "ms",
        "timezone": "GMT",
        "models": "era5",
    }, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload.get("reason", "ERA5 archive request failed"))
    hourly = payload["hourly"]
    speed = np.asarray([
        float(value) if value is not None else np.nan
        for value in hourly["wind_speed_10m"]
    ])
    direction = np.asarray([
        float(value) if value is not None else np.nan
        for value in hourly["wind_direction_10m"]
    ])
    radians = np.radians(direction)
    u = -speed * np.sin(radians)
    v = -speed * np.cos(radians)
    stamp = pd.to_datetime(hourly["time"], utc=True)
    east, east_times = backward_match(stamp, u, times, max_age_hours=0)
    north, north_times = backward_match(stamp, v, times, max_age_hours=0)
    return {"wind_u": east, "wind_v": north}, {
        "wind_u": east_times, "wind_v": north_times,
    }


def build(root, output, max_observations=3):
    if not 1 <= max_observations <= 12:
        raise ValueError("--max-observations must be in [1, 12]")
    selections = cached_observations(root, max_observations)
    if not selections:
        raise ValueError("No completed cached marine batches with valid observations")
    session = requests.Session()
    records = []
    for ix, obs in enumerate(selections, start=1):
        hours = hourly_grid(obs["time"])
        folder = obs["folder"]
        currents, current_times = grid_history(
            folder / "marine" / "currents_pilot.nc", obs, hours,
            {"current_u": "uo", "current_v": "vo"}, max_age_hours=30,
        )
        waves, wave_times = grid_history(
            folder / "marine" / "waves_pilot.nc", obs, hours,
            {"stokes_u": "VSDX", "stokes_v": "VSDY"}, max_age_hours=3,
        )
        wind, wind_times = wind_history(obs, hours, session)
        values = {**currents, **waves, **wind}
        sources = {**current_times, **wave_times, **wind_times}
        result = summarize_history(values, obs["time"])
        result.update({
            "ID": obs["ID"],
            "sample_latitude": obs["latitude"],
            "sample_longitude": obs["longitude"],
            "batch": folder.name,
            "earliest_hour": hours[0].isoformat(),
            "latest_hour": hours[-1].isoformat(),
            "source_time_after_observation": any(
                ts is not None and pd.Timestamp(ts) > hours[-1]
                for column in CHANNELS for ts in sources[column]
            ),
        })
        if result["source_time_after_observation"]:
            raise ValueError("A source timestamp exceeded the observation time")
        records.append(result)
        print(f"Temporal observation {ix}/{len(selections)}: "
              f"{result['valid_hours']}/{HOURS} valid hours")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(records)
    frame.to_csv(output / "temporal_pilot.csv", index=False)
    report = {
        "observations": int(len(frame)),
        "distinct_drifters": int(frame["ID"].nunique()),
        "complete_observations": int(frame["complete"].sum()),
        "future_labeled_source_samples": int(frame["source_time_after_observation"].sum()),
        "source_policy": "backward timestamps only, fixed observed anchor; wind hourly, wave <=3h, daily current <=30h",
        "production_ready": False,
        "limitations": [
            "Historical datasets are retrospective; timestamps are not publication-time availability guarantees.",
            "GLORYS daily-mean currents can include data from later in the calendar day.",
            "Fixed observation-point histories do not constitute an advected 24-hour trajectory.",
            "No model V3 training is performed by this pilot.",
        ],
    }
    (output / "coverage_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="data/interim/diverse")
    parser.add_argument("--output", default="data/interim/temporal_pilot")
    parser.add_argument("--max-observations", type=int, default=3)
    args = parser.parse_args()
    build(args.root, args.output, args.max_observations)


if __name__ == "__main__":
    main()
