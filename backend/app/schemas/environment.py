from typing import Literal

from pydantic import BaseModel


class EnvironmentData(BaseModel):
    """
    Environmental conditions collected for an observation.

    This schema represents real historical weather data retrieved
    from Open-Meteo and will later be extended with marine,
    satellite, and AI-derived information.
    """

    temperature: float

    wind_speed: float

    wind_gust: float

    wind_direction: float

    wind_direction_text: str

    weather_code: int

    weather_state: str

    precipitation: float

    provider: Literal["Open-Meteo"]

    source_version: str