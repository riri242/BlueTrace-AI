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
from app.services.object_detection_service import ObjectDetectionService
from app.services.location_classifier import LocationClassifier


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_IMAGE_BYTES = 10 * 1024 * 1024


# ---------------------------------------------------------
# Image Validation
# ---------------------------------------------------------

async def validate_image_upload(
    image: UploadFile,
) -> ImageMetadata:

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


# ---------------------------------------------------------
# Main Analysis Pipeline
# ---------------------------------------------------------

async def create_analysis_response(
    payload: AnalysisRequest,
    image: UploadFile,
) -> AnalysisResponse:

    # --------------------------------------------
    # Validate upload
    # --------------------------------------------

    image_metadata = await validate_image_upload(image)

    # --------------------------------------------
    # Save image temporarily
    # --------------------------------------------

    suffix = Path(image.filename).suffix

    with NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp_file:

        temp_path = Path(temp_file.name)

        image_bytes = await image.read()

        temp_file.write(image_bytes)

    await image.seek(0)

    try:

        # ----------------------------------------
        # YOLO Object Detection
        # ----------------------------------------

        detector = ObjectDetectionService()

        detections = detector.detect(
            image_path=str(temp_path),
        )

        # ----------------------------------------
        # Environment
        # ----------------------------------------

        environment_service = EnvironmentService()

        environment = await environment_service.get_environment(
            latitude=payload.latitude,
            longitude=payload.longitude,
            date=payload.date.isoformat(),
            time=payload.time.strftime("%H:%M"),
        )

        # ----------------------------------------
        # Location Classification
        # ----------------------------------------

        classifier = LocationClassifier()

        prediction = classifier.classify(
            detections=detections,
            environment=environment,
        )

    finally:

        if temp_path.exists():
            temp_path.unlink()

    # --------------------------------------------
    # Final Response
    # --------------------------------------------

    return AnalysisResponse(
        status="success",
        message="Analysis completed successfully.",
        received=ReceivedPayload(
            date=payload.date.isoformat(),
            time=payload.time.isoformat(timespec="minutes"),
            latitude=payload.latitude,
            longitude=payload.longitude,
            image=image_metadata,
        ),
        environment=environment,
        detections=detections,
        prediction=prediction,
    )