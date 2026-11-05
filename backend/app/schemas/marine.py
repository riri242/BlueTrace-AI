from pydantic import BaseModel


class MarineData(BaseModel):
    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None
    ocean_current_velocity: float | None = None
    ocean_current_direction: float | None = None
    sea_surface_temperature: float | None = None
    provider: str
    source_version: str
    observed_at: str
