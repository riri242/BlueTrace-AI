import logging
from typing import Any

from app.utils.location_profiles import LOCATION_PROFILES

logger = logging.getLogger(__name__)


class LocationClassifier:
    """
    BlueTrace AI Location Classification Engine

    Milestone 5

    Combines:
        • YOLO detections
        • Weather
        • Temperature
        • Wind
        • Rain

    to estimate the most probable image origin.
    """

    OBJECT_WEIGHT = 4.0
    WEATHER_WEIGHT = 3.0
    TEMPERATURE_WEIGHT = 2.0
    WIND_WEIGHT = 2.0
    RAIN_WEIGHT = 1.0

    def classify(
        self,
        detections: list[dict[str, Any]],
        environment: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Classify the uploaded image into one of the predefined
        BlueTrace locations.
        """

        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = {}

        for location_name, profile in LOCATION_PROFILES.items():

            score = 0.0
            reason: list[str] = []

            object_score, object_reason = self._score_objects(
                detections,
                profile,
            )
            score += object_score
            reason.extend(object_reason)

            weather_score, weather_reason = self._score_weather(
                environment,
                profile,
            )
            score += weather_score
            reason.extend(weather_reason)

            temp_score, temp_reason = self._score_temperature(
                environment,
                profile,
            )
            score += temp_score
            reason.extend(temp_reason)

            wind_score, wind_reason = self._score_wind(
                environment,
                profile,
            )
            score += wind_score
            reason.extend(wind_reason)

            rain_score, rain_reason = self._score_rain(
                environment,
                profile,
            )
            score += rain_score
            reason.extend(rain_reason)

            score *= profile.get("priority", 1.0)

            scores[location_name] = round(score, 2)
            reasons[location_name] = reason

        best_location = max(scores, key=scores.get)
        best_score = scores[best_location]

        total_score = sum(scores.values())

        confidence = (
            round((best_score / total_score) * 100, 1)
            if total_score > 0
            else 0.0
        )

        logger.info(
            "Prediction: %s | Confidence: %.1f%% | Score: %.2f",
            best_location,
            confidence,
            best_score,
        )

        logger.info("Scores: %s", scores)

        return {
            "predicted_location": best_location,
            "confidence": confidence,
            "score": best_score,
            "reasoning": reasons[best_location],
            "all_scores": scores,
        }

    # ==========================================================
    # Object Score
    # ==========================================================

    def _score_objects(
        self,
        detections: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> tuple[float, list[str]]:

        score = 0.0
        reason: list[str] = []

        expected = profile.get("expected_objects", [])

        if not expected:
            return score, reason

        for detection in detections:

            class_name = detection.get("class_name")
            confidence = float(detection.get("confidence", 0))

            if class_name in expected:

                score += confidence * self.OBJECT_WEIGHT

                reason.append(f"Detected {class_name}")

        return score, reason

    # ==========================================================
    # Weather Score
    # ==========================================================

    def _score_weather(
        self,
        environment: dict[str, Any],
        profile: dict[str, Any],
    ) -> tuple[float, list[str]]:

        score = 0.0
        reason: list[str] = []

        state = environment.get("weather_state")

        if state in profile.get("preferred_weather", []):

            score += self.WEATHER_WEIGHT

            reason.append(f"Weather matches ({state})")

        return score, reason

    # ==========================================================
    # Temperature Score
    # ==========================================================

    def _score_temperature(
        self,
        environment: dict[str, Any],
        profile: dict[str, Any],
    ) -> tuple[float, list[str]]:

        score = 0.0
        reason: list[str] = []

        temp = environment.get("temperature")

        if temp is None:
            return score, reason

        low, high = profile.get("temperature", (-100, 100))

        if low <= temp <= high:

            score += self.TEMPERATURE_WEIGHT

            reason.append("Temperature in expected range")

        return score, reason

    # ==========================================================
    # Wind Score
    # ==========================================================

    def _score_wind(
        self,
        environment: dict[str, Any],
        profile: dict[str, Any],
    ) -> tuple[float, list[str]]:

        score = 0.0
        reason: list[str] = []

        wind = environment.get("wind_speed")

        if wind is None:
            return score, reason

        low, high = profile.get("wind_speed", (0, 200))

        if low <= wind <= high:

            score += self.WIND_WEIGHT

            reason.append("Wind speed matches")

        return score, reason

    # ==========================================================
    # Rain Score
    # ==========================================================

    def _score_rain(
        self,
        environment: dict[str, Any],
        profile: dict[str, Any],
    ) -> tuple[float, list[str]]:

        score = 0.0
        reason: list[str] = []

        rain = environment.get("precipitation")

        if rain is None:
            return score, reason

        low, high = profile.get("precipitation", (0, 1000))

        if low <= rain <= high:

            score += self.RAIN_WEIGHT

            reason.append("Precipitation matches")

        return score, reason