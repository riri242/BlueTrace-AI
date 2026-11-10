"""Exploratory 24-hour backward Euler advection over gridded marine fields.

Uses nearest spatial ocean cells and latest grid label not after step time.
Historical daily mean products can include later hours in their averaging
period; grid labels are not operational release timestamps.
No coastline collisions, leeway calibration, or debris classification.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .dataset import EARTH_KM, haversine_km


@dataclass(frozen=True)
class TraceResult:
    status: str
    path: tuple[dict, ...]
    steps: int
    reason: str | None = None


def advance_backward(lat, lon, u, v, seconds=3600):
    """Subtract east/north velocity (m/s) over one backward step."""
    if not np.isfinite([lat, lon, u, v, seconds]).all() or seconds <= 0:
        raise ValueError("Finite coordinates, velocity and positive step are required")
    if not -90 < lat < 90:
        raise ValueError("Latitude cannot be at a pole")
    north_km = -v * seconds / 1000
    east_km = -u * seconds / 1000
    next_lat = lat + np.degrees(north_km / EARTH_KM)
    cosine = np.cos(np.radians((lat + next_lat) / 2))
    if abs(cosine) < 1e-6:
        raise ValueError("Longitude is undefined near the pole")
    next_lon = lon + np.degrees(east_km / (EARTH_KM * cosine))
    return float(next_lat), float(next_lon)


class MarineGrid:
    """Adapter for cached GLORYS current and WAVERYS Stokes datasets."""

    def __init__(self, currents, waves, *, max_distance_degrees=0.4):
        self.currents = currents
        self.waves = waves
        self.max_distance_degrees = float(max_distance_degrees)
        if self.max_distance_degrees <= 0:
            raise ValueError("max_distance_degrees must be positive")

    def _sample(self, data, fields, when, lat, lon, max_age_hours):
        label = pd.Timestamp(when)
        if label.tzinfo is None:
            raise ValueError("Requested time must have a UTC offset")
        label = label.tz_convert("UTC")
        stamps = pd.DatetimeIndex(pd.to_datetime(data["time"].values, utc=True))
        if not stamps.is_monotonic_increasing:
            raise ValueError("Marine time coordinates are not ordered")
        position = stamps.searchsorted(label, side="right") - 1
        if position < 0:
            raise ValueError("No marine measurement at or before requested time")
        age = (label - stamps[position]).total_seconds() / 3600
        if age < 0 or age > max_age_hours:
            raise ValueError("Marine measurement is too old")

        latitude = np.asarray(data["latitude"].values, dtype=float)
        longitude = np.asarray(data["longitude"].values, dtype=float)
        if not (latitude.min() <= lat <= latitude.max()
                and longitude.min() <= lon <= longitude.max()):
            raise ValueError("Trajectory moved outside cached marine grid")
        point = data.isel(time=int(position)).sel(
            latitude=float(lat), longitude=float(lon), method="nearest"
        )
        sample_lat = float(point["latitude"].item())
        sample_lon = float(point["longitude"].item())
        if np.hypot(sample_lat - lat, (sample_lon - lon) * np.cos(np.radians(lat))) > self.max_distance_degrees:
            raise ValueError("Nearest ocean cell is too far from trajectory point")
        result = []
        for variable in fields:
            cell = point[variable]
            if "depth" in cell.dims:
                cell = cell.isel(depth=0)
            value = float(cell.item())
            if not np.isfinite(value):
                raise ValueError(f"Missing ocean value: {variable}")
            result.append(value)
        return result, stamps[position].isoformat()

    def velocity(self, when, lat, lon, *, include_stokes=True):
        current, current_time = self._sample(
            self.currents, ("uo", "vo"), when, lat, lon, max_age_hours=30
        )
        if not include_stokes:
            return current[0], current[1], {"current_source_time": current_time}
        stokes, wave_time = self._sample(
            self.waves, ("VSDX", "VSDY"), when, lat, lon, max_age_hours=3
        )
        return current[0] + stokes[0], current[1] + stokes[1], {
            "current_source_time": current_time,
            "wave_source_time": wave_time,
        }


def backtrack(start_lat, start_lon, observation_time, grid, *,
              hours=24, include_stokes=True, wind=None, windage=0.0):
    """Integrate backwards while updating position at each hourly step.

    Optional wind is a dict of ISO UTC hour -> (east, north) in m/s; it is
    sampled at the observation anchor, not dynamically along the trajectory.
    Default windage=0 excludes wind-induced leeway.
    """
    if not 1 <= hours <= 168:
        raise ValueError("hours must be within 1..168")
    if not 0 <= windage <= 0.1:
        raise ValueError("windage must be within 0..0.1")
    if windage and wind is None:
        raise ValueError("wind time series required when windage is enabled")
    moment = pd.Timestamp(observation_time)
    if moment.tzinfo is None:
        raise ValueError("Observation timestamp must be timezone aware")
    moment = moment.tz_convert("UTC")
    if moment.minute or moment.second or moment.microsecond:
        raise ValueError("Observation timestamp must be on an hour")
    lat, lon = float(start_lat), float(start_lon)
    path = [{"time": moment.isoformat(), "latitude": lat, "longitude": lon}]
    for step in range(hours):
        when = moment - pd.Timedelta(hours=step)
        try:
            u, v, provenance = grid.velocity(
                when, lat, lon, include_stokes=include_stokes
            )
            if windage:
                wind_pair = wind.get(when.isoformat())
                if wind_pair is None or not np.isfinite(wind_pair).all():
                    raise ValueError("Hourly wind data unavailable")
                u += windage * float(wind_pair[0])
                v += windage * float(wind_pair[1])
            lat, lon = advance_backward(lat, lon, u, v)
            if not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError("Invalid integrated coordinates")
        except ValueError as error:
            return TraceResult("incomplete", tuple(path), step, str(error))
        path.append({
            "time": (when - pd.Timedelta(hours=1)).isoformat(),
            "latitude": lat, "longitude": lon, **provenance,
        })
    return TraceResult("complete", tuple(path), hours)


def score_trace(trace, true_lat, true_lon):
    if trace.status != "complete":
        return None
    last = trace.path[-1]
    return float(haversine_km(
        true_lat, true_lon, last["latitude"], last["longitude"]
    ))
