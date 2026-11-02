import logging
from datetime import datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class MarineService:
    BASE_URL = "https://marine-api.open-meteo.com/v1/marine"
    TIMEOUT_SECONDS = 15.0
    HOURLY_VARIABLES = (
        "wave_height",
        "wave_direction",
        "wave_period",
        "ocean_current_velocity",
        "ocean_current_direction",
        "sea_surface_temperature",
    )

    async def get_marine(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
    ) -> dict[str, Any]:
        target = datetime.fromisoformat(f"{date}T{time}")
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": date,
            "end_date": date,
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "America/Los_Angeles",
            "cell_selection": "sea",
        }

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            raise RuntimeError("Marine data request failed.") from exc

        if not isinstance(data, dict) or data.get("error"):
            raise RuntimeError("Marine data is unavailable for the selected date.")

        hourly = data.get("hourly")
        if not isinstance(hourly, dict):
            raise ValueError("Marine response is missing hourly data.")

        timestamps = hourly.get("time")
        if not isinstance(timestamps, list) or not timestamps:
            raise ValueError("Marine response is missing hourly timestamps.")

        try:
            index = min(
                range(len(timestamps)),
                key=lambda i: abs(
                    (datetime.fromisoformat(timestamps[i]) - target).total_seconds()
                ),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("Marine response contains invalid timestamps.") from exc

        values = {}
        for field in self.HOURLY_VARIABLES:
            series = hourly.get(field)
            value = series[index] if isinstance(series, list) and index < len(series) else None
            values[field] = (
                float(value)
                if isinstance(value, (int, float)) and not isinstance(value, bool)
                else None
            )

        if all(value is None for value in values.values()):
            raise ValueError("No marine observations are available for the selected time.")

        return {
            **values,
            "provider": "Open-Meteo",
            "source_version": "Marine Weather API",
            "observed_at": timestamps[index],
        }

    async def get_marine_history(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
        hours: int = 24,
    ) -> dict[str, Any]:
        if not isinstance(hours, int) or isinstance(hours, bool) or not 1 <= hours <= 72:
            raise ValueError("History window must be between 1 and 72 hours.")

        from datetime import timedelta

        target = datetime.fromisoformat(f"{date}T{time}")
        start = target - timedelta(hours=hours)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start.date().isoformat(),
            "end_date": target.date().isoformat(),
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "timezone": "America/Los_Angeles",
            "cell_selection": "sea",
        }

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError, ValueError) as exc:
            raise RuntimeError("Marine history request failed.") from exc

        if not isinstance(data, dict) or data.get("error"):
            raise RuntimeError("Marine history is unavailable for the selected period.")

        hourly = data.get("hourly")
        if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
            raise ValueError("Marine history response is missing hourly timestamps.")

        observations = []
        for index, timestamp in enumerate(hourly["time"]):
            try:
                observed_at = datetime.fromisoformat(timestamp)
            except (TypeError, ValueError) as exc:
                raise ValueError("Marine history contains invalid timestamps.") from exc

            if not start <= observed_at <= target:
                continue

            values = {}
            for field in self.HOURLY_VARIABLES:
                series = hourly.get(field)
                value = series[index] if isinstance(series, list) and index < len(series) else None
                values[field] = (
                    float(value)
                    if isinstance(value, (int, float)) and not isinstance(value, bool)
                    else None
                )
            if any(value is not None for value in values.values()):
                observations.append({"observed_at": timestamp, **values})

        if not observations:
            raise ValueError("No marine history is available for the selected period.")

        observations.sort(key=lambda observation: observation["observed_at"])
        return {
            "provider": "Open-Meteo",
            "source_version": "Marine Weather API",
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "America/Los_Angeles",
            "start_at": start.isoformat(timespec="minutes"),
            "end_at": target.isoformat(timespec="minutes"),
            "hours_requested": hours,
            "units": {
                "wave_height": "m",
                "wave_direction": "degrees",
                "wave_period": "s",
                "ocean_current_velocity": "km/h",
                "ocean_current_direction": "degrees",
                "sea_surface_temperature": "°C",
            },
            "observations": observations,
        }
