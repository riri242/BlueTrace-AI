"""Load NOAA trajectories and build independent, strictly hourly backtracking labels."""

from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = ("ID", "time", "latitude", "longitude")
EARTH_KM = 6371.0088


def read_noaa(path: str | Path) -> pd.DataFrame:
    source = Path(path)
    data = pd.read_csv(source)
    if "time" in data and str(data.iloc[0]["time"]).strip() == "UTC":
        data = data.iloc[1:].copy()
    missing = set(COLUMNS) - set(data.columns)
    if missing:
        raise ValueError(f"Missing NOAA columns: {sorted(missing)}")
    for col in ("latitude", "longitude"):
        data[col] = pd.to_numeric(data[col], errors="raise")
    data["time"] = pd.to_datetime(data["time"], utc=True, errors="raise")
    if data[list(COLUMNS)].isna().any().any():
        raise ValueError("NOAA ID, timestamp, and coordinates must not be missing")
    if not data["latitude"].between(-90, 90).all() or not data["longitude"].between(-180, 180).all():
        raise ValueError("Invalid NOAA coordinates")
    if data.duplicated(["ID", "time"]).any():
        raise ValueError("Duplicate NOAA drifter ID/time records")
    return data.sort_values(["ID", "time"]).reset_index(drop=True)


def make_24h_pairs(data: pd.DataFrame, hours: int = 24) -> pd.DataFrame:
    if hours < 1:
        raise ValueError("horizon must be positive")
    ordered = data.sort_values(["ID", "time"]).reset_index(drop=True).copy()
    grouped = ordered.groupby("ID", sort=False)
    previous_time = grouped["time"].shift(hours)
    previous_lat = grouped["latitude"].shift(hours)
    previous_lon = grouped["longitude"].shift(hours)
    valid = (ordered["time"] - previous_time).eq(pd.Timedelta(hours=hours))
    pairs = ordered.loc[valid].copy()
    pairs["previous_latitude"] = previous_lat[valid].to_numpy()
    pairs["previous_longitude"] = previous_lon[valid].to_numpy()
    latitude_radians = np.radians(pairs["latitude"].to_numpy())
    pairs["target_east_km"] = (pairs["previous_longitude"].to_numpy() - pairs["longitude"].to_numpy()) * (np.pi / 180) * EARTH_KM * np.cos(latitude_radians)
    pairs["target_north_km"] = (pairs["previous_latitude"].to_numpy() - pairs["latitude"].to_numpy()) * (np.pi / 180) * EARTH_KM
    return pairs.reset_index(drop=True)


def target_to_coordinates(data: pd.DataFrame, offset_km: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    lat = data["latitude"].to_numpy() + np.degrees(offset_km[:, 1] / EARTH_KM)
    lon = data["longitude"].to_numpy() + np.degrees(
        offset_km[:, 0] / (EARTH_KM * np.cos(np.radians(data["latitude"].to_numpy())))
    )
    return lat, lon


def haversine_km(lat_a, lon_a, lat_b, lon_b):
    a1, a2 = np.radians(np.asarray(lat_a)), np.radians(np.asarray(lat_b))
    dlat = a2 - a1
    dlon = np.radians(np.asarray(lon_b) - np.asarray(lon_a))
    h = np.sin(dlat / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_KM * np.arcsin(np.sqrt(np.clip(h, 0, 1)))
