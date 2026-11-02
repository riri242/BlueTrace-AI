import unittest
from unittest.mock import patch

from app.services.marine_service import MarineService


class MarineHistoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_history_filters_window_and_preserves_order(self):
        payload = {
            "hourly": {
                "time": [
                    "2026-10-22T08:00",
                    "2026-10-22T09:00",
                    "2026-10-23T09:00",
                    "2026-10-23T10:00",
                ],
                "wave_height": [0.5, 1.0, 1.5, 2.0],
                "ocean_current_velocity": [0.1, 0.2, 0.3, 0.4],
            }
        }
        captured = {}

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return payload

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, url, params):
                captured.update(params)
                return Response()

        with patch("app.services.marine_service.httpx.AsyncClient", return_value=Client()):
            result = await MarineService().get_marine_history(
                latitude=36.9,
                longitude=-121.8,
                date="2026-10-23",
                time="09:43",
                hours=24,
            )

        self.assertEqual(captured["start_date"], "2026-10-22")
        self.assertEqual(captured["end_date"], "2026-10-23")
        self.assertEqual(len(result["observations"]), 2)
        self.assertEqual(result["observations"][0]["observed_at"], "2026-10-22T09:00")
        self.assertEqual(result["observations"][1]["observed_at"], "2026-10-23T09:00")
        self.assertEqual(result["observations"][1]["ocean_current_velocity"], 0.3)

    async def test_rejects_invalid_history_window(self):
        for hours in (0, 73, True):
            with self.subTest(hours=hours):
                with self.assertRaises(ValueError):
                    await MarineService().get_marine_history(
                        latitude=36.9,
                        longitude=-121.8,
                        date="2026-10-23",
                        time="09:43",
                        hours=hours,
                    )

    async def test_rejects_missing_observations(self):
        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"hourly": {"time": ["2026-10-23T09:00"], "wave_height": [None]}}

        class Client:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def get(self, *args, **kwargs):
                return Response()

        with patch("app.services.marine_service.httpx.AsyncClient", return_value=Client()):
            with self.assertRaises(ValueError):
                await MarineService().get_marine_history(
                    latitude=36.9,
                    longitude=-121.8,
                    date="2026-10-23",
                    time="09:43",
                )


if __name__ == "__main__":
    unittest.main()
