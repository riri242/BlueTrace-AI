import unittest

from pydantic import ValidationError

from app.schemas.analysis import AnalysisRequest
from app.schemas.drift import DriftRequest
from app.utils.geo import CALIFORNIA_COAST_BOUNDS


class CaliforniaCoastBoundsTests(unittest.TestCase):
    def test_study_area_bounds(self):
        bounds = CALIFORNIA_COAST_BOUNDS
        self.assertEqual((bounds.latitude_min, bounds.latitude_max), (32.0, 42.0))
        self.assertEqual((bounds.longitude_min, bounds.longitude_max), (-125.0, -117.0))

    def test_southern_and_northern_california_accepted(self):
        for latitude, longitude in ((32.7, -117.3), (40.7, -124.3)):
            with self.subTest(latitude=latitude):
                request = DriftRequest(date="2022-10-01", time="12:00",
                                       latitude=latitude, longitude=longitude)
                self.assertEqual(request.latitude, latitude)
                analysis = AnalysisRequest(date="2022-10-01", time="12:00",
                                           latitude=latitude, longitude=longitude)
                self.assertEqual(analysis.longitude, longitude)

    def test_outside_bounds_rejected(self):
        for latitude, longitude in ((31.9, -120.0), (42.1, -124.0),
                                    (35.0, -125.1), (35.0, -116.9)):
            with self.subTest(latitude=latitude, longitude=longitude):
                with self.assertRaises(ValidationError):
                    DriftRequest(date="2022-10-01", time="12:00",
                                 latitude=latitude, longitude=longitude)
                with self.assertRaises(ValidationError):
                    AnalysisRequest(date="2022-10-01", time="12:00",
                                    latitude=latitude, longitude=longitude)


if __name__ == "__main__":
    unittest.main()
