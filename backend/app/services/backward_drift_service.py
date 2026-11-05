import math
from datetime import datetime
from typing import Any

from app.services.marine_history_preprocessor import prepare_marine_history

EARTH_RADIUS_KM = 6371.0088
MAX_GAP_HOURS = 1.5


def estimate_backward_drift(history: dict[str, Any]) -> dict[str, Any]:
    prepared = prepare_marine_history(history)
    latitude = prepared["latitude"]
    longitude = prepared["longitude"]
    if not all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in (latitude, longitude)
    ) or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("A valid observation location is required.")

    readings = prepared["observations"]
    if len(readings) < 2:
        raise ValueError("At least two current observations are required.")

    latitude = float(latitude)
    longitude = float(longitude)
    anchor = datetime.fromisoformat(readings[-1]["observed_at"])
    points = [{"observed_at": anchor.isoformat(timespec="minutes"),
               "latitude": latitude, "longitude": longitude}]
    integrated_hours = 0.0

    for older, newer in zip(reversed(readings[:-1]), reversed(readings[1:])):
        older_time = datetime.fromisoformat(older["observed_at"])
        newer_time = datetime.fromisoformat(newer["observed_at"])
        duration_hours = (newer_time - older_time).total_seconds() / 3600
        if not 0 < duration_hours <= MAX_GAP_HOURS:
            break

        speed = newer["ocean_current_velocity_kmh"]
        direction = math.radians(newer["ocean_current_direction_deg"])
        distance_km = speed * duration_hours
        north_km = distance_km * math.cos(direction)
        east_km = distance_km * math.sin(direction)
        latitude -= math.degrees(north_km / EARTH_RADIUS_KM)
        cosine = math.cos(math.radians(latitude))
        if abs(cosine) < 1e-6:
            raise ValueError("Longitude cannot be estimated near the poles.")
        longitude -= math.degrees(east_km / (EARTH_RADIUS_KM * cosine))
        longitude = ((longitude + 180) % 360) - 180

        integrated_hours += duration_hours
        points.append({
            "observed_at": older_time.isoformat(timespec="minutes"),
            "latitude": round(latitude, 6),
            "longitude": round(longitude, 6),
        })

    if not integrated_hours:
        raise ValueError("Insufficient contiguous hourly current observations.")

    return {
        "method": "fixed-location-current-only-backward-euler",
        "status": "experimental",
        "anchor_time": anchor.isoformat(timespec="minutes"),
        "hours_traced": integrated_hours,
        "path": points,
        "limitations": (
            "Exploratory current-only displacement from a fixed observation location. "
            "Not a validated debris-source prediction. Wind, waves, coastlines, "
            "spatially varying currents, and observation-to-sample time offset "
            "are not modeled."
        ),
    }
