from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.geo import MONTEREY_BAY_BOUNDS


class DriftRequest(BaseModel):
    date: date
    time: time
    latitude: float = Field(ge=MONTEREY_BAY_BOUNDS.latitude_min, le=MONTEREY_BAY_BOUNDS.latitude_max)
    longitude: float = Field(ge=MONTEREY_BAY_BOUNDS.longitude_min, le=MONTEREY_BAY_BOUNDS.longitude_max)
    hours: int = Field(default=24, ge=1, le=72)

    @field_validator("hours", mode="before")
    @classmethod
    def reject_boolean_hours(cls, value):
        if isinstance(value, bool):
            raise ValueError("hours must be an integer")
        return value


class DriftPoint(BaseModel):
    observed_at: str
    latitude: float
    longitude: float


class DriftResponse(BaseModel):
    status: Literal["experimental", "unavailable"]
    observation_date: str
    observation_time: str
    hours_requested: int
    hours_traced: float = 0
    source: str = "Open-Meteo Marine Weather API"
    method: str = "fixed-location-current-only-backward-euler"
    path: list[DriftPoint] = Field(default_factory=list)
    message: str
    limitations: str
