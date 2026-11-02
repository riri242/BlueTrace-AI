import logging
from typing import Any

from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class EnvironmentService:
    def __init__(self, weather_service: WeatherService | None = None) -> None:
        self.weather_service = weather_service or WeatherService()

    async def get_environment(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
    ) -> dict[str, Any] | None:
        try:
            return await self.weather_service.get_weather(
                latitude=latitude,
                longitude=longitude,
                date=date,
                time=time,
            )
        except (RuntimeError, ValueError) as exc:
            logger.warning("Weather data unavailable: %s", exc)
            return None
