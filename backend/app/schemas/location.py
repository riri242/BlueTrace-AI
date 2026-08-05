from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class LocationPrediction(BaseModel):
    """
    Final prediction returned by the BlueTrace AI classifier.
    """

    predicted_location: str = Field(
        ...,
        description="Most probable origin of the uploaded image.",
        examples=["Sandy Beach"],
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=100,
        description="Prediction confidence percentage.",
        examples=[91.4],
    )

    score: float = Field(
        ...,
        ge=0,
        description="Internal classifier score.",
        examples=[18.7],
    )

    reasoning: List[str] = Field(
        default_factory=list,
        description="Human-readable explanation of the prediction.",
        examples=[
            [
                "Detected boat",
                "Detected bird",
                "Weather matches (Overcast)",
                "Wind speed matches",
            ]
        ],
    )

    all_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Score assigned to every candidate location.",
        examples=[
            {
                "Sandy Beach": 18.7,
                "Rocky Shore": 14.2,
                "Harbor": 11.8,
                "Wetland": 9.4,
                "Urban Coast": 6.1,
                "Cliff Coast": 5.0,
                "Unknown": 0.0,
            }
        ],
    )


class PredictionResponse(BaseModel):
    """
    Complete response for the location prediction stage.
    """

    status: Literal["success"]

    message: str

    prediction: LocationPrediction