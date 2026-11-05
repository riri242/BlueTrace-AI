import unittest
from unittest.mock import AsyncMock

from app.services.environment_service import EnvironmentService
from app.services.marine_service import MarineService


class MarineServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_extracts_nearest_hour(self):
        service = MarineService()
        data = {
            "hourly": {
                "time": ["2026-10-23T09:00", "2026-10-23T10:00"],
                "wave_height": [1.2, 1.5],
                "wave_direction": [250, 255],
                "wave_period": [8, 9],
                "ocean_current_velocity": [0.2, 0.3],
                "ocean_current_direction": [180, 190],
                "sea_surface_temperature": [14.0, 14.1],
            }
        }

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return data

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, *args, **kwargs):
                return Response()

        from unittest.mock import patch

        with patch("app.services.marine_service.httpx.AsyncClient", return_value=Client()):
            result = await service.get_marine(
                latitude=36.9,
                longitude=-121.8,
                date="2026-10-23",
                time="09:43",
            )

        self.assertEqual(result["wave_height"], 1.5)
        self.assertEqual(result["ocean_current_velocity"], 0.3)

    async def test_preserves_weather_when_marine_fails(self):
        weather = AsyncMock()
        weather.get_weather.return_value = {"temperature": 17}
        marine = AsyncMock()
        marine.get_marine.side_effect = RuntimeError("Service unavailable")

        result = await EnvironmentService(weather, marine).get_environment(
            latitude=36.9,
            longitude=-121.8,
            date="2026-10-23",
            time="09:43",
        )

        self.assertEqual(result["weather"]["temperature"], 17)
        self.assertIsNone(result["marine"])


if __name__ == "__main__":
    unittest.main()
