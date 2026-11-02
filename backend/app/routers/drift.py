from fastapi import APIRouter

from app.schemas.drift import DriftRequest, DriftResponse
from app.services.drift_pipeline import calculate_drift

router = APIRouter(prefix="/drift", tags=["drift"])


@router.post("/estimate", response_model=DriftResponse)
async def estimate_drift(payload: DriftRequest) -> DriftResponse:
    result = await calculate_drift(payload)
    return DriftResponse.model_validate(result)
