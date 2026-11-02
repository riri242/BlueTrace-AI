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
