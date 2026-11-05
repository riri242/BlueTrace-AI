import json
import tempfile
import unittest
from pathlib import Path

from app.services.coastline_validation import check_coastline


class CoastlineScreeningTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.dataset = Path(self.directory.name) / "land.geojson"
        self.dataset.write_text(json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "properties": {},
                "geometry": {"type": "Polygon", "coordinates": [[
                    [-121.9, 36.8], [-121.8, 36.8],
                    [-121.8, 36.9], [-121.9, 36.9], [-121.9, 36.8]
                ]]}
            }]
        }), encoding="utf-8")

    def test_segment_crosses_land(self):
        path = [{"longitude": -121.95, "latitude": 36.85},
                {"longitude": -121.75, "latitude": 36.85}]
        self.assertEqual(check_coastline(path, str(self.dataset)), "potential_land_crossing")

    def test_segment_avoids_land(self):
        path = [{"longitude": -122.1, "latitude": 36.85},
                {"longitude": -122.0, "latitude": 36.85}]
        self.assertEqual(check_coastline(path, str(self.dataset)), "clear_on_reference_map")

    def test_missing_reference_is_not_clear(self):
        path = [{"longitude": -122.1, "latitude": 36.85},
                {"longitude": -122.0, "latitude": 36.85}]
        self.assertEqual(check_coastline(path, "/nonexistent/land.geojson"), "not_checked")


if __name__ == "__main__":
    unittest.main()
