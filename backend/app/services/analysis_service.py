from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import HTTPException, UploadFile, status

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ImageMetadata,
    ReceivedPayload,
)
from app.services.environment_service import EnvironmentService
from app.services.location_classifier import LocationClassifier
from app.services.object_detection_service import ObjectDetectionService

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
            detail="Image must be JPEG, PNG or WebP.",
        )

    contents = await image.read(MAX_IMAGE_BYTES + 1)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Image cannot be empty.",
        )

    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum image size is 10 MB.",
        )

    await image.seek(0)
    return ImageMetadata(
        filename=image.filename,
        content_type=image.content_type,
        size_bytes=len(contents),
    )


async def create_analysis_response(
    payload: AnalysisRequest,
    image: UploadFile,
) -> AnalysisResponse:
    image_metadata = await validate_image_upload(image)
    suffix = Path(image.filename).suffix

    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = Path(temp_file.name)
        temp_file.write(await image.read())

    await image.seek(0)

    try:
        detections = ObjectDetectionService().detect(image_path=str(temp_path))
        conditions = await EnvironmentService().get_environment(
            latitude=payload.latitude,
            longitude=payload.longitude,
            date=payload.date.isoformat(),
            time=payload.time.strftime("%H:%M"),
        )
        weather = conditions["weather"]
        marine = conditions["marine"]
        prediction = (
            LocationClassifier().classify(
                detections=detections,
                environment=weather,
            )
            if weather is not None
            else None
        )
    finally:
        temp_path.unlink(missing_ok=True)

    if weather is not None and marine is not None:
        message = "Analysis completed successfully."
    elif weather is None and marine is None:
        message = "Object detection completed. Weather and marine data are unavailable."
    else:
        message = "Object detection completed. Some environmental data is unavailable."

    return AnalysisResponse(
        status="success",
        message=message,
        received=ReceivedPayload(
            date=payload.date.isoformat(),
            time=payload.time.isoformat(timespec="minutes"),
            latitude=payload.latitude,
            longitude=payload.longitude,
            image=image_metadata,
        ),
        environment=weather,
        marine=marine,
        detections=detections,
        prediction=prediction,
    )
