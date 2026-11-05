import unittest
from unittest.mock import AsyncMock

from app.services.environment_service import EnvironmentService


class EnvironmentServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.weather_provider = AsyncMock()
        self.marine_provider = AsyncMock()
        self.marine_provider.get_marine.return_value = {"wave_height": 1.5}
        self.service = EnvironmentService(
            weather_service=self.weather_provider,
            marine_service=self.marine_provider,
        )
        self.request = {
            "latitude": 36.6,
            "longitude": -121.9,
            "date": "2025-10-25",
            "time": "12:00",
        }

    async def test_returns_weather_and_marine_data(self):
        weather = {"temperature": 18.0, "provider": "Open-Meteo"}
        self.weather_provider.get_weather.return_value = weather

        result = await self.service.get_environment(**self.request)

        self.assertEqual(result["weather"], weather)
        self.assertEqual(result["marine"], {"wave_height": 1.5})
        self.weather_provider.get_weather.assert_awaited_once_with(**self.request)
        self.marine_provider.get_marine.assert_awaited_once_with(**self.request)

    async def test_preserves_marine_when_weather_times_out(self):
        self.weather_provider.get_weather.side_effect = RuntimeError(
            "Open-Meteo request timed out."
        )

        result = await self.service.get_environment(**self.request)

        self.assertIsNone(result["weather"])
        self.assertEqual(result["marine"], {"wave_height": 1.5})

    async def test_preserves_marine_when_weather_data_is_invalid(self):
        self.weather_provider.get_weather.side_effect = ValueError(
            "Open-Meteo response does not contain hourly weather data."
        )

        result = await self.service.get_environment(**self.request)

        self.assertIsNone(result["weather"])
        self.assertEqual(result["marine"], {"wave_height": 1.5})


if __name__ == "__main__":
    unittest.main()
