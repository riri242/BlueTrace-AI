from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.utils.geo import CALIFORNIA_COAST_BOUNDS


class DriftRequest(BaseModel):
    date: date
    time: time
    latitude: float = Field(ge=CALIFORNIA_COAST_BOUNDS.latitude_min, le=CALIFORNIA_COAST_BOUNDS.latitude_max)
    longitude: float = Field(ge=CALIFORNIA_COAST_BOUNDS.longitude_min, le=CALIFORNIA_COAST_BOUNDS.longitude_max)
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
    anchor_time: str | None = None
    observation_offset_minutes: float | None = None
    coastline_status: Literal["not_checked", "potential_land_crossing", "clear_on_reference_map"] = "not_checked"
    source: str = "Open-Meteo Marine Weather API"
    method: str = "fixed-location-current-only-backward-euler"
    path: list[DriftPoint] = Field(default_factory=list)
    message: str
    limitations: str
