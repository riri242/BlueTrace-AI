from datetime import date as DateType
from datetime import time as TimeType

from typing import Literal

from pydantic import BaseModel, Field

from app.utils.geo import MONTEREY_BAY_BOUNDS


class AnalysisRequest(BaseModel):
    date: DateType
    time: TimeType
    latitude: float = Field(
        ...,
        ge=MONTEREY_BAY_BOUNDS.latitude_min,
        le=MONTEREY_BAY_BOUNDS.latitude_max,
    )
    longitude: float = Field(
        ...,
        ge=MONTEREY_BAY_BOUNDS.longitude_min,
        le=MONTEREY_BAY_BOUNDS.longitude_max,
    )


class ImageMetadata(BaseModel):
    filename: str
    content_type: str
    size_bytes: int


class ReceivedPayload(BaseModel):
    date: str
    time: str
    latitude: float
    longitude: float
    image: ImageMetadata


class AnalysisResponse(BaseModel):
    status: Literal["success"]
    message: str
    received: ReceivedPayload
