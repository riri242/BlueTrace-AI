import unittest

from app.services.backward_drift_service import estimate_backward_drift


class DriftReferenceCases(unittest.TestCase):
    def estimate(self, speed, direction, hours=1):
        from datetime import datetime, timedelta
        end = datetime(2026, 10, 23, 9)
        observations = [
            {"observed_at": (end - timedelta(hours=i)).isoformat(timespec="minutes"),
             "ocean_current_velocity": speed, "ocean_current_direction": direction}
            for i in range(hours, -1, -1)
        ]
        return estimate_backward_drift({
            "latitude": 36.9, "longitude": -121.8,
            "units": {"ocean_current_velocity": "km/h"},
            "observations": observations,
        })

    def test_stationary_current_stays_at_anchor(self):
        result = self.estimate(0, 0, hours=3)
        self.assertEqual(result["hours_traced"], 3)
        self.assertTrue(all(point["latitude"] == 36.9 for point in result["path"]))
        self.assertTrue(all(point["longitude"] == -121.8 for point in result["path"]))

    def test_one_kmh_northward_for_one_hour_is_about_nine_millidegrees_south(self):
        result = self.estimate(1, 0)
        self.assertAlmostEqual(result["path"][-1]["latitude"], 36.891007, places=5)
        self.assertAlmostEqual(result["path"][-1]["longitude"], -121.8, places=5)

    def test_eastward_current_backtracks_west(self):
        result = self.estimate(1, 90)
        self.assertLess(result["path"][-1]["longitude"], -121.8)
        self.assertAlmostEqual(result["path"][-1]["latitude"], 36.9, places=5)


if __name__ == "__main__":
    unittest.main()
