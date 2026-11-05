from pydantic import BaseModel


class GeoBounds(BaseModel):
    latitude_min: float
    latitude_max: float
    longitude_min: float
    longitude_max: float


CALIFORNIA_COAST_BOUNDS = GeoBounds(
    latitude_min=32.0,
    latitude_max=42.0,
    longitude_min=-125.0,
    longitude_max=-117.0,
)
