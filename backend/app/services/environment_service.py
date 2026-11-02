import logging
from typing import Any

from app.services.marine_service import MarineService
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)


class EnvironmentService:
    def __init__(
        self,
        weather_service: WeatherService | None = None,
        marine_service: MarineService | None = None,
    ) -> None:
        self.weather_service = weather_service or WeatherService()
        self.marine_service = marine_service or MarineService()

    async def get_environment(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
    ) -> dict[str, Any]:
        conditions: dict[str, Any] = {"weather": None, "marine": None}

        for name, service, method in (
            ("weather", self.weather_service, "get_weather"),
            ("marine", self.marine_service, "get_marine"),
        ):
            try:
                conditions[name] = await getattr(service, method)(
                    latitude=latitude,
                    longitude=longitude,
                    date=date,
                    time=time,
                )
            except (RuntimeError, ValueError) as exc:
                logger.warning("%s data unavailable: %s", name.capitalize(), exc)

        return conditions
