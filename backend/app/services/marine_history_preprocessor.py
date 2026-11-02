from datetime import datetime
from typing import Any


def prepare_marine_history(history: dict[str, Any]) -> dict[str, Any]:
    observations = history.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("Marine history has no observations.")

    prepared = []
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("Marine history contains an invalid observation.")

        timestamp = observation.get("observed_at")
        try:
            observed_at = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError) as exc:
            raise ValueError("Marine history contains an invalid timestamp.") from exc

        velocity = observation.get("ocean_current_velocity")
        direction = observation.get("ocean_current_direction")
        if (
            not isinstance(velocity, (int, float))
            or isinstance(velocity, bool)
            or not isinstance(direction, (int, float))
            or isinstance(direction, bool)
        ):
            continue

        if not 0 <= direction <= 360 or velocity < 0:
            continue

        prepared.append({
            "observed_at": observed_at,
            "ocean_current_velocity_kmh": float(velocity),
            "ocean_current_direction_deg": float(direction),
            "wave_height_m": observation.get("wave_height"),
            "wave_direction_deg": observation.get("wave_direction"),
            "wave_period_s": observation.get("wave_period"),
            "sea_surface_temperature_c": observation.get("sea_surface_temperature"),
        })

    prepared.sort(key=lambda item: item["observed_at"])
    if not prepared:
        raise ValueError("Marine history has no usable current observations.")

    for previous, current in zip(prepared, prepared[1:]):
        if current["observed_at"] == previous["observed_at"]:
            raise ValueError("Marine history contains duplicate timestamps.")

    return {
        "latitude": history.get("latitude"),
        "longitude": history.get("longitude"),
        "timezone": history.get("timezone"),
        "units": {
            "ocean_current_velocity": "km/h",
            "ocean_current_direction": "degrees",
            "wave_height": "m",
            "wave_direction": "degrees",
            "wave_period": "s",
            "sea_surface_temperature": "°C",
        },
        "observation_count": len(prepared),
        "observations": [
            {**item, "observed_at": item["observed_at"].isoformat(timespec="minutes")}
            for item in prepared
        ],
    }
