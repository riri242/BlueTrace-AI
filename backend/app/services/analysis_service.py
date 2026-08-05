from fastapi import HTTPException, UploadFile, status

from app.services.environment_service import EnvironmentService

from app.schemas.analysis import (
  AnalysisRequest,
  AnalysisResponse,
  ImageMetadata,
  ReceivedPayload
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


async def validate_image_upload(image: UploadFile) -> ImageMetadata:
    if not image.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image filename is required.",
        )

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image must be a JPEG, PNG, or WebP file.",
        )

    contents = await image.read(MAX_IMAGE_BYTES + 1)

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image file cannot be empty.",
        )

    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 10 MB or smaller.",
        )

    await image.seek(0)

    return ImageMetadata(
        content_type=image.content_type,
        filename=image.filename,
        size_bytes=len(contents),
    )

async def create_analysis_response(
    payload: AnalysisRequest,
    image: UploadFile,
) -> AnalysisResponse:
    """
    Validate the uploaded image, retrieve historical environmental
    conditions for the selected observation, and return the analysis
    response.
    """

    # Validate uploaded image
    image_metadata = await validate_image_upload(image)

    # Retrieve environmental conditions
    environment_service = EnvironmentService()

    environment = await environment_service.get_environment(
        latitude=payload.latitude,
        longitude=payload.longitude,
        date=payload.date.isoformat(),
        time=payload.time.strftime("%H:%M"),
    )

    # Return response
    return AnalysisResponse(
        status="success",
        message="Environmental conditions retrieved successfully.",
        received=ReceivedPayload(
            date=payload.date.isoformat(),
            image=image_metadata,
            latitude=payload.latitude,
            longitude=payload.longitude,
            time=payload.time.isoformat(timespec="minutes"),
        ),
        environment=environment,
    )