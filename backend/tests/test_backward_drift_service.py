import unittest

from app.services.backward_drift_service import estimate_backward_drift


class BackwardDriftTests(unittest.TestCase):
    def test_northward_current_moves_estimate_south(self):
        result = estimate_backward_drift({
            "latitude": 36.9,
            "longitude": -121.8,
            "observations": [
                {"observed_at": "2026-10-23T08:00", "ocean_current_velocity": 1, "ocean_current_direction": 0},
                {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 1, "ocean_current_direction": 0},
            ],
        })
        self.assertEqual(result["hours_traced"], 1)
        self.assertLess(result["path"][-1]["latitude"], 36.9)
        self.assertEqual(result["status"], "experimental")

    def test_eastward_current_moves_estimate_west(self):
        result = estimate_backward_drift({
            "latitude": 36.9,
            "longitude": -121.8,
            "observations": [
                {"observed_at": "2026-10-23T08:00", "ocean_current_velocity": 1, "ocean_current_direction": 90},
                {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 1, "ocean_current_direction": 90},
            ],
        })
        self.assertLess(result["path"][-1]["longitude"], -121.8)

    def test_stops_at_gap_in_hourly_readings(self):
        with self.assertRaises(ValueError):
            estimate_backward_drift({
                "latitude": 36.9,
                "longitude": -121.8,
                "observations": [
                    {"observed_at": "2026-10-23T06:00", "ocean_current_velocity": 1, "ocean_current_direction": 0},
                    {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 1, "ocean_current_direction": 0},
                ],
            })


if __name__ == "__main__":
    unittest.main()
