import { useEffect, useRef } from "react";
import mapboxgl, { type Map as MapboxMap } from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";

import type { DriftPoint } from "@/types/drift";

type CoastlineStatus = "potential_land_crossing" | "clear_on_reference_map" | "not_checked";

const TOKEN = import.meta.env.VITE_MAPBOX_TOKEN?.trim() ?? "";

export function DriftPathMap({ path, coastlineStatus }: { path: DriftPoint[]; coastlineStatus?: CoastlineStatus }) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapboxMap | null>(null);

  useEffect(() => {
    if (!containerRef.current || !TOKEN || path.length < 2) return;
    mapboxgl.accessToken = TOKEN;
    const map = new mapboxgl.Map({
      container: containerRef.current,
      style: document.documentElement.classList.contains("dark")
        ? "mapbox://styles/mapbox/navigation-night-v1"
        : "mapbox://styles/mapbox/navigation-day-v1",
      center: [path[0].longitude, path[0].latitude],
      zoom: 10
    });
    mapRef.current = map;
    const handleThemeChange = (event: Event) => {
      const theme = (event as CustomEvent<"dark" | "light">).detail;
      map.setStyle(theme === "dark"
        ? "mapbox://styles/mapbox/navigation-night-v1"
        : "mapbox://styles/mapbox/navigation-day-v1");
    };
    window.addEventListener("bluetrace-theme-change", handleThemeChange);
    const points = path.map((point) => [point.longitude, point.latitude] as [number, number]);
    const sourceId = "drift-path";
    const start = new mapboxgl.Marker({ color: "#146f94" }).setLngLat(points[0]).addTo(map);
    const end = new mapboxgl.Marker({ color: "#dc6a2d" }).setLngLat(points[points.length - 1]).addTo(map);
    const onLoad = () => {
      map.addSource(sourceId, {
        type: "geojson",
        data: {
          type: "Feature",
          properties: {},
          geometry: { type: "LineString", coordinates: points }
        }
      });
      map.addLayer({
        id: sourceId,
        type: "line",
        source: sourceId,
        paint: { "line-color": "#dc6a2d", "line-width": 4, "line-opacity": 0.85 }
      });
      const bounds = points.reduce((acc, point) => acc.extend(point), new mapboxgl.LngLatBounds(points[0], points[0]));
      map.fitBounds(bounds, { padding: 55, maxZoom: 12 });
    };
    map.on("load", onLoad);
    return () => {
      window.removeEventListener("bluetrace-theme-change", handleThemeChange);
      map.off("load", onLoad);
      start.remove();
      end.remove();
      map.remove();
      mapRef.current = null;
    };
  }, [path]);

  if (!TOKEN || path.length < 2) return null;

  return (
    <div className="mt-5 space-y-2">
      <div ref={containerRef} className="h-80 w-full overflow-hidden rounded-2xl border border-research-line" aria-label="Experimental backward drift route map" />
      <p className="text-sm text-research-muted">
        Blue marker: observation anchor. Orange marker: oldest calculated position. {coastlineStatus === "potential_land_crossing"
          ? "This experimental line intersects mapped land and is not a valid marine trajectory."
          : coastlineStatus === "clear_on_reference_map"
            ? "No land crossing was detected on the reference map. This experimental line is not a verified marine route."
            : "Coastline screening was not completed. This experimental line is not a verified marine route."}
      </p>
    </div>
  );
}
