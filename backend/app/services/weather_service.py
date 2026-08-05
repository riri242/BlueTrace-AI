"""
weather_service.py

Retrieves historical hourly weather data for BlueTrace AI using
the Open-Meteo Historical Forecast API.

Responsibilities:
- Request historical weather for a selected location and date.
- Find the hourly record closest to the user's observation time.
- Convert WMO weather codes into readable descriptions.
- Convert wind direction degrees into compass directions.
- Return normalized environmental data for EnvironmentService.

This service does not write to the database. Persistence belongs
to the database/service layer.
"""

from datetime import datetime
from typing import Any

import httpx

from app.utils.weather_codes import weather_code_to_text
from app.utils.wind import degrees_to_compass


class WeatherService:
    """Service for retrieving historical weather data from Open-Meteo."""

    BASE_URL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    PROVIDER = "Open-Meteo"
    SOURCE_VERSION = "Historical Forecast API"
    REQUEST_TIMEOUT_SECONDS = 20.0

    HOURLY_VARIABLES = (
        "temperature_2m",
        "weather_code",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
        "precipitation",
    )

    async def get_weather(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
    ) -> dict[str, Any]:
        """
        Retrieve weather conditions nearest to the observation time.

        Args:
            latitude: Observation latitude.
            longitude: Observation longitude.
            date: Observation date in YYYY-MM-DD format.
            time: Observation time in HH:MM format.

        Returns:
            A normalized dictionary containing weather conditions.

        Raises:
            ValueError: If inputs or returned weather data are invalid.
            RuntimeError: If Open-Meteo cannot be reached or returns an error.
        """
        self._validate_coordinates(latitude, longitude)
        self._validate_date(date)
        self._validate_time(time)

        params = self._build_params(
            latitude=latitude,
            longitude=longitude,
            date=date,
        )

        data = await self._request_weather(params)

        return self._extract_weather(
            data=data,
            observation_date=date,
            observation_time=time,
        )

    def _build_params(
        self,
        latitude: float,
        longitude: float,
        date: str,
    ) -> dict[str, Any]:
        """Build query parameters for Open-Meteo."""
        return {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join(self.HOURLY_VARIABLES),
            "start_date": date,
            "end_date": date,
            "timezone": "auto",
        }

    async def _request_weather(
        self,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the Open-Meteo HTTP request."""
        try:
            async with httpx.AsyncClient(
                timeout=self.REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Open-Meteo request timed out."
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            raise RuntimeError(
                f"Open-Meteo returned HTTP {status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                "Unable to connect to Open-Meteo."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Open-Meteo returned an invalid JSON response."
            ) from exc

        if not isinstance(data, dict):
            raise RuntimeError(
                "Open-Meteo returned an unexpected response format."
            )

        return data

    def _extract_weather(
        self,
        data: dict[str, Any],
        observation_date: str,
        observation_time: str,
    ) -> dict[str, Any]:
        """Extract the hourly weather record nearest to the observation."""
        hourly = data.get("hourly")

        if not isinstance(hourly, dict):
            raise ValueError(
                "Open-Meteo response does not contain hourly weather data."
            )

        timestamps = hourly.get("time")

        if not isinstance(timestamps, list) or not timestamps:
            raise ValueError(
                "Open-Meteo response does not contain hourly timestamps."
            )

        self._validate_hourly_fields(hourly, len(timestamps))

        target_datetime = datetime.fromisoformat(
            f"{observation_date}T{observation_time}"
        )

        closest_index = self._find_closest_time_index(
            timestamps=timestamps,
            target_datetime=target_datetime,
        )

        temperature = self._get_hourly_value(
            hourly,
            "temperature_2m",
            closest_index,
        )

        weather_code_value = self._get_hourly_value(
            hourly,
            "weather_code",
            closest_index,
        )

        wind_speed = self._get_hourly_value(
            hourly,
            "wind_speed_10m",
            closest_index,
        )

        wind_direction = self._get_hourly_value(
            hourly,
            "wind_direction_10m",
            closest_index,
        )

        wind_gust = self._get_hourly_value(
            hourly,
            "wind_gusts_10m",
            closest_index,
        )

        precipitation = self._get_hourly_value(
            hourly,
            "precipitation",
            closest_index,
        )

        if weather_code_value is None:
            raise ValueError(
                "Weather code is missing for the selected observation time."
            )

        weather_code = int(weather_code_value)

        return {
            "temperature": self._require_number(
                temperature,
                "temperature",
            ),
            "wind_speed": self._require_number(
                wind_speed,
                "wind speed",
            ),
            "wind_gust": self._require_number(
                wind_gust,
                "wind gust",
            ),
            "wind_direction": self._require_number(
                wind_direction,
                "wind direction",
            ),
            "wind_direction_text": degrees_to_compass(
                self._require_number(
                    wind_direction,
                    "wind direction",
                )
            ),
            "weather_code": weather_code,
            "weather_state": weather_code_to_text(weather_code),
            "precipitation": self._require_number(
                precipitation,
                "precipitation",
            ),
            "provider": self.PROVIDER,
            "source_version": self.SOURCE_VERSION,
        }

    def _find_closest_time_index(
        self,
        timestamps: list[Any],
        target_datetime: datetime,
    ) -> int:
        """Return the index of the timestamp closest to the target time."""
        closest_index: int | None = None
        smallest_difference: float | None = None

        for index, timestamp in enumerate(timestamps):
            if not isinstance(timestamp, str):
                continue

            try:
                timestamp_datetime = datetime.fromisoformat(timestamp)
            except ValueError:
                continue

            difference = abs(
                (timestamp_datetime - target_datetime).total_seconds()
            )

            if (
                smallest_difference is None
                or difference < smallest_difference
            ):
                smallest_difference = difference
                closest_index = index

        if closest_index is None:
            raise ValueError(
                "No valid hourly timestamp was returned by Open-Meteo."
            )

        return closest_index

    def _validate_hourly_fields(
        self,
        hourly: dict[str, Any],
        expected_length: int,
    ) -> None:
        """Ensure required hourly variables exist and align with timestamps."""
        for field in self.HOURLY_VARIABLES:
            values = hourly.get(field)

            if not isinstance(values, list):
                raise ValueError(
                    f"Open-Meteo response is missing hourly field '{field}'."
                )

            if len(values) != expected_length:
                raise ValueError(
                    f"Hourly field '{field}' has an unexpected length."
                )

    @staticmethod
    def _get_hourly_value(
        hourly: dict[str, Any],
        field: str,
        index: int,
    ) -> Any:
        """Safely retrieve a value from an hourly data array."""
        values = hourly.get(field)

        if not isinstance(values, list):
            raise ValueError(
                f"Hourly field '{field}' is unavailable."
            )

        if index >= len(values):
            raise ValueError(
                f"Hourly field '{field}' does not contain the selected time."
            )

        return values[index]

    @staticmethod
    def _require_number(
        value: Any,
        field_name: str,
    ) -> float:
        """Validate and normalize a numeric API value."""
        if value is None or isinstance(value, bool):
            raise ValueError(
                f"Open-Meteo returned no valid {field_name} value."
            )

        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Open-Meteo returned an invalid {field_name} value."
            )

        return float(value)

    @staticmethod
    def _validate_coordinates(
        latitude: float,
        longitude: float,
    ) -> None:
        """Validate geographic coordinates."""
        if not -90 <= latitude <= 90:
            raise ValueError(
                "Latitude must be between -90 and 90."
            )

        if not -180 <= longitude <= 180:
            raise ValueError(
                "Longitude must be between -180 and 180."
            )

    @staticmethod
    def _validate_date(value: str) -> None:
        """Validate YYYY-MM-DD date input."""
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(
                "Date must use YYYY-MM-DD format."
            ) from exc

    @staticmethod
    def _validate_time(value: str) -> None:
        """Validate HH:MM time input."""
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError(
                "Time must use HH:MM format."
            ) from exc