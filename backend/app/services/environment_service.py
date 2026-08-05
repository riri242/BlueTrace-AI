from app.services.weather_service import WeatherService


class EnvironmentService:
    """
    Coordinates all environmental data providers.

    Currently:
        - Open-Meteo Historical Weather

    Future:
        - NOAA
        - Marine Forecast
        - Ocean Currents
        - Wave Height
        - Satellite Imagery
    """

    def __init__(self):
        self.weather_service = WeatherService()

    async def get_environment(
        self,
        latitude: float,
        longitude: float,
        date: str,
        time: str,
    ):

        weather = await self.weather_service.get_weather(
            latitude=latitude,
            longitude=longitude,
            date=date,
            time=time,
        )

        return weather