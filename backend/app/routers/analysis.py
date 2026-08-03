from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import create_analysis_response

router = APIRouter(tags=["analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_submission(
    image: UploadFile = File(...),
    date: str = Form(...),
    time: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
) -> AnalysisResponse:
    try:
        payload = AnalysisRequest.model_validate(
            {
                "date": date,
                "time": time,
                "latitude": latitude,
                "longitude": longitude,
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(),
        ) from exc

    return await create_analysis_response(payload, image)
