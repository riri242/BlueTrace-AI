import unittest

from app.services.marine_history_preprocessor import prepare_marine_history


class MarineHistoryPreprocessorTests(unittest.TestCase):
    def test_sorts_and_filters_unusable_currents(self):
        result = prepare_marine_history({
            "latitude": 36.9,
            "longitude": -121.8,
            "timezone": "America/Los_Angeles",
            "observations": [
                {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 0.3, "ocean_current_direction": 315, "wave_height": 1.2},
                {"observed_at": "2026-10-23T08:00", "ocean_current_velocity": 0.2, "ocean_current_direction": 300},
                {"observed_at": "2026-10-23T07:00", "ocean_current_velocity": None, "ocean_current_direction": 270},
            ],
        })

        self.assertEqual(result["observation_count"], 2)
        self.assertEqual(result["observations"][0]["observed_at"], "2026-10-23T08:00")
        self.assertEqual(result["observations"][1]["ocean_current_velocity_kmh"], 0.3)

    def test_converts_meters_per_second_to_kmh(self):
        result = prepare_marine_history({
            "units": {"ocean_current_velocity": "m/s"},
            "observations": [
                {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 1, "ocean_current_direction": 90}
            ]
        })
        self.assertAlmostEqual(result["observations"][0]["ocean_current_velocity_kmh"], 3.6)

    def test_rejects_missing_current_data(self):
        with self.assertRaises(ValueError):
            prepare_marine_history({
                "observations": [
                    {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": None, "ocean_current_direction": 270}
                ]
            })

    def test_rejects_duplicate_timestamps(self):
        with self.assertRaises(ValueError):
            prepare_marine_history({
                "observations": [
                    {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 0.2, "ocean_current_direction": 270},
                    {"observed_at": "2026-10-23T09:00", "ocean_current_velocity": 0.3, "ocean_current_direction": 280},
                ]
            })


if __name__ == "__main__":
    unittest.main()
