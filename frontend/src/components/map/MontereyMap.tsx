import { useEffect, useRef } from "react";
import mapboxgl, {
  type LngLatBoundsLike,
  type LngLatLike,
  type Map as MapboxMap,
  type Marker
} from "mapbox-gl";
import type { MutableRefObject } from "react";
import "mapbox-gl/dist/mapbox-gl.css";

import type { Coordinates } from "@/types/analysis";

interface MontereyMapProps {
  error?: string;
  onChange: (coordinates: Coordinates) => void;
  value: Coordinates | null;
}

const MONTEREY_BAY_CENTER: LngLatLike = [-121.93, 36.8];
const MONTEREY_BAY_BOUNDS: LngLatBoundsLike = [
  [-122.32, 36.42],
  [-121.68, 37.12]
];

function setMarker(
  map: MapboxMap,
  markerRef: MutableRefObject<Marker | null>,
  coordinates: Coordinates
) {
  const lngLat: [number, number] = [coordinates.longitude, coordinates.latitude];

  if (!markerRef.current) {
    markerRef.current = new mapboxgl.Marker({ color: "#146f94" })
      .setLngLat(lngLat)
      .addTo(map);
    return;
  }

  markerRef.current.setLngLat(lngLat);
}

export function MontereyMap({ error, onChange, value }: MontereyMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapboxMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const onChangeRef = useRef(onChange);
  const token = import.meta.env.VITE_MAPBOX_TOKEN;

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    if (!token || !containerRef.current || mapRef.current) {
      return;
    }

    mapboxgl.accessToken = token;

    const map = new mapboxgl.Map({
      center: MONTEREY_BAY_CENTER,
      container: containerRef.current,
      dragRotate: false,
      maxBounds: MONTEREY_BAY_BOUNDS,
      maxZoom: 13.5,
      minZoom: 8.25,
      pitchWithRotate: false,
      style: "mapbox://styles/mapbox/light-v11",
      zoom: 9.1
    });

    map.touchZoomRotate.disableRotation();
    map.addControl(
      new mapboxgl.NavigationControl({
        showCompass: false,
        showZoom: true,
        visualizePitch: false
      }),
      "top-right"
    );

    map.on("click", (event) => {
      const coordinates = {
        latitude: Number(event.lngLat.lat.toFixed(6)),
        longitude: Number(event.lngLat.lng.toFixed(6))
      };

      setMarker(map, markerRef, coordinates);
      onChangeRef.current(coordinates);
    });

    mapRef.current = map;

    return () => {
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, [token]);

  useEffect(() => {
    if (!value || !mapRef.current) {
      return;
    }

    setMarker(mapRef.current, markerRef, value);
    mapRef.current.easeTo({
      center: [value.longitude, value.latitude],
      duration: 450
    });
  }, [value]);

  return (
    <div className="space-y-4">
      <div
        className="relative h-[24rem] overflow-hidden rounded-2xl border border-research-line bg-ocean-50"
        id="monterey-map"
      >
        {token ? (
          <div className="h-full w-full" ref={containerRef} />
        ) : (
          <div className="flex h-full items-center justify-center p-8 text-center">
            <p className="max-w-sm text-sm leading-6 text-research-muted">
              Set VITE_MAPBOX_TOKEN to enable the Monterey Bay location map.
            </p>
          </div>
        )}
      </div>

      {value ? (
        <dl className="grid grid-cols-1 gap-3 rounded-2xl border border-ocean-100 bg-ocean-50/75 p-4 text-sm sm:grid-cols-2">
          <div>
            <dt className="font-medium text-research-muted">Latitude</dt>
            <dd className="mt-1 font-semibold text-research-ink">
              {value.latitude.toFixed(6)}
            </dd>
          </div>
          <div>
            <dt className="font-medium text-research-muted">Longitude</dt>
            <dd className="mt-1 font-semibold text-research-ink">
              {value.longitude.toFixed(6)}
            </dd>
          </div>
        </dl>
      ) : (
        <p className="text-sm leading-6 text-research-muted">
          Click once inside Monterey Bay, California to save latitude and
          longitude.
        </p>
      )}

      {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}
    </div>
  );
}
