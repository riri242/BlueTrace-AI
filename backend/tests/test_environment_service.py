import unittest
from unittest.mock import AsyncMock

from app.services.environment_service import EnvironmentService


class EnvironmentServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_weather_data(self):
        weather = {"temperature": 18.0, "provider": "Open-Meteo"}
        provider = AsyncMock()
        provider.get_weather.return_value = weather

        result = await EnvironmentService(provider).get_environment(
            latitude=36.6,
            longitude=-121.9,
            date="2025-10-25",
            time="12:00",
        )

        self.assertEqual(result, weather)
        provider.get_weather.assert_awaited_once()

    async def test_returns_none_when_provider_times_out(self):
        provider = AsyncMock()
        provider.get_weather.side_effect = RuntimeError(
            "Open-Meteo request timed out."
        )

        result = await EnvironmentService(provider).get_environment(
            latitude=36.6,
            longitude=-121.9,
            date="2025-10-25",
            time="12:00",
        )

        self.assertIsNone(result)

    async def test_returns_none_for_invalid_provider_data(self):
        provider = AsyncMock()
        provider.get_weather.side_effect = ValueError(
            "Open-Meteo response does not contain hourly weather data."
        )

        result = await EnvironmentService(provider).get_environment(
            latitude=36.6,
            longitude=-121.9,
            date="2025-10-25",
            time="12:00",
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
