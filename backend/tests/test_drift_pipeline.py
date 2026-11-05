import unittest
from datetime import date, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.drift import DriftRequest
from app.services.drift_pipeline import calculate_drift


class FakeMarineService:
    async def get_marine_history(self, latitude, longitude, date, time, hours):
        anchor = datetime.fromisoformat(f"{date}T{time}").replace(minute=0, second=0, microsecond=0)
        return {
            "latitude": latitude,
            "longitude": longitude,
            "observations": [
                {"observed_at": (anchor - timedelta(hours=1)).isoformat(timespec="minutes"),
                 "ocean_current_velocity": 0.3, "ocean_current_direction": 90},
                {"observed_at": anchor.isoformat(timespec="minutes"),
                 "ocean_current_velocity": 0.3, "ocean_current_direction": 90},
            ],
        }


class MissingMarineService:
    async def get_marine_history(self, **kwargs):
        raise RuntimeError("No historical coverage")


class DriftPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_uses_observation_date_instead_of_upload_date(self):
        payload = DriftRequest(date=date(2026, 10, 23), time="09:43",
                               latitude=36.9, longitude=-121.8, hours=24)
        result = await calculate_drift(payload, FakeMarineService())
        self.assertEqual(result["status"], "experimental")
        self.assertEqual(result["observation_date"], "2026-10-23")
        self.assertEqual(result["hours_traced"], 1)

    async def test_missing_history_returns_unavailable(self):
        payload = DriftRequest(date=date(2026, 10, 23), time="09:43",
                               latitude=36.9, longitude=-121.8)
        result = await calculate_drift(payload, MissingMarineService())
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result.get("path", []), [])

    async def test_future_date_returns_unavailable(self):
        payload = DriftRequest(date=date(2099, 1, 1), time="12:00",
                               latitude=36.9, longitude=-121.8)
        result = await calculate_drift(payload, FakeMarineService())
        self.assertEqual(result["status"], "unavailable")


class DriftAPITests(unittest.TestCase):
    def test_invalid_coordinates_rejected(self):
        with TestClient(app) as client:
            response = client.post("/api/v1/drift/estimate", json={
                "date": "2026-10-23", "time": "09:43",
                "latitude": 90, "longitude": -121.8, "hours": 24,
            })
        self.assertEqual(response.status_code, 422)

    def test_invalid_hours_rejected(self):
        with TestClient(app) as client:
            response = client.post("/api/v1/drift/estimate", json={
                "date": "2026-10-23", "time": "09:43",
                "latitude": 36.9, "longitude": -121.8, "hours": 73,
            })
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
