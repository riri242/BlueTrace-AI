"""Conservative California coast screening using WGS84 land polygons.

Set BLUETRACE_LAND_GEOJSON to override the local data/monterey_land.geojson. A missing
or unreadable dataset never produces a 'clear' verdict. This is screening, not
a shoreline collision model.
"""
import json
import os
from pathlib import Path


def check_coastline(path: list[dict], dataset_path: str | None = None) -> str:
    default_dataset = Path(__file__).resolve().parents[2] / "data" / "monterey_land.geojson"
    dataset = dataset_path or os.getenv("BLUETRACE_LAND_GEOJSON") or str(default_dataset)
    if not dataset or not Path(dataset).is_file() or len(path) < 2:
        return "not_checked"
    try:
        from shapely.geometry import LineString, Point, shape
        from shapely.ops import unary_union

        data = json.loads(Path(dataset).read_text(encoding="utf-8"))
        if data.get("type") == "FeatureCollection":
            geometries = [shape(feature["geometry"]) for feature in data["features"] if feature.get("geometry")]
        elif data.get("type") == "Feature":
            geometries = [shape(data["geometry"])]
        else:
            geometries = [shape(data)]
        polygons = [geometry for geometry in geometries if geometry.geom_type in ("Polygon", "MultiPolygon")]
        if not polygons:
            return "not_checked"
        land = unary_union(polygons)
        line = LineString([(point["longitude"], point["latitude"]) for point in path])
        return "potential_land_crossing" if land.intersects(line) else "clear_on_reference_map"
    except (OSError, ValueError, TypeError, KeyError, ImportError):
        return "not_checked"
