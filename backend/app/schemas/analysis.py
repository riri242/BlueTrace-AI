from datetime import date as DateType
from datetime import time as TimeType
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.environment import EnvironmentData
from app.schemas.location import LocationPrediction
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


class Detection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    category: str
    blue_trace_relevance: str

    bounding_box: dict[str, float]


class AnalysisResponse(BaseModel):
    status: Literal["success"]

    message: str

    received: ReceivedPayload

    environment: EnvironmentData | None = None

    detections: list[Detection] = Field(
        default_factory=list,
        description="Objects detected by the YOLO model.",
    )

    prediction: LocationPrediction | None = None