from typing import Any, Dict, List

from ultralytics import YOLO

from app.utils.blue_trace_categories import BLUE_TRACE_CATEGORIES

# ==========================================================
# BlueTrace AI - Object Detection Service
# ==========================================================

MODEL_NAME = "yolo11n.pt"

# Load the YOLO model once when FastAPI starts
model = YOLO(MODEL_NAME)

# ----------------------------------------------------------
# Default metadata for unknown objects
# ----------------------------------------------------------

DEFAULT_METADATA = {
    "category": "Unknown",
    "material": "Unknown",
    "floats": False,
    "buoyancy": "Unknown",
    "drift_potential": "Unknown",
    "likely_source": [],
    "transport_mode": [],
    "environmental_risk": "Unknown",
    "estimated_persistence_years": None,
}


class ObjectDetectionService:
    """
    Performs object detection using a pretrained YOLO11 model.
    """

    def detect(
        self,
        image_path: str,
        confidence_threshold: float = 0.25,
    ) -> List[Dict[str, Any]]:

        results = model.predict(
            source=image_path,
            conf=confidence_threshold,
            verbose=False,
        )

        detections: List[Dict[str, Any]] = []

        for result in results:

            for box in result.boxes:

                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                confidence = float(box.conf[0])

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                # --------------------------------------------------
                # Copy metadata so we never modify the original
                # knowledge base accidentally.
                # --------------------------------------------------

                metadata = BLUE_TRACE_CATEGORIES.get(
                    class_name,
                    DEFAULT_METADATA,
                ).copy()

                detections.append(
                    {
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": round(confidence, 3),
                        "bounding_box": {
                            "x1": round(x1, 1),
                            "y1": round(y1, 1),
                            "x2": round(x2, 1),
                            "y2": round(y2, 1),
                        },
                        "blue_trace": metadata,
                    }
                )

        return detections