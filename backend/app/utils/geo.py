from pydantic import BaseModel


class GeoBounds(BaseModel):
    latitude_min: float
    latitude_max: float
    longitude_min: float
    longitude_max: float


MONTEREY_BAY_BOUNDS = GeoBounds(
    latitude_min=36.42,
    latitude_max=37.12,
    longitude_min=-122.32,
    longitude_max=-121.68,
)
