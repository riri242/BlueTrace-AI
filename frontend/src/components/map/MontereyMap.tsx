import { useEffect, useRef, useState } from "react";
import mapboxgl, {
  type LngLatBoundsLike,
  type LngLatLike,
  type Map as MapboxMap,
  type MapMouseEvent,
  type Marker
} from "mapbox-gl";
import type { MutableRefObject } from "react";
import "mapbox-gl/dist/mapbox-gl.css";

import type { Coordinates } from "@/types/analysis";

interface MontereyMapProps {
  /** Allows page-level layout tweaks while keeping the map behavior reusable. */
  className?: string;
  /** Displays parent form validation beneath the coordinate selector. */
  error?: string;
  /** Optional DOM id for labels, analytics, or end-to-end tests. */
  id?: string;
  /** Emits the selected California coast observation coordinates to the parent. */
  onChange: (coordinates: Coordinates) => void;
  /** Controlled marker position. Pass null to clear the current marker. */
  value: Coordinates | null;
}

type MapStatus = "loading" | "ready" | "error";

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN?.trim() ?? "";
const DAY_STYLE = "mapbox://styles/mapbox/navigation-day-v1";
const NIGHT_STYLE = "mapbox://styles/mapbox/navigation-night-v1";
const CALIFORNIA_COAST_CENTER: LngLatLike = [-121.2, 37.0];

// Study-area bounds keep the marker workflow focused on California coast only.
const CALIFORNIA_COAST_BOUNDS: LngLatBoundsLike = [
  [-125.0, 32.0],
  [-117.0, 42.0]
];
const INITIAL_ZOOM = 5.1;
const MIN_ZOOM = 4.5;
const MAX_ZOOM = 13.25;

function createObservationMarkerElement() {
  const marker = document.createElement("div");
  marker.setAttribute("aria-label", "Selected observation site");
  marker.style.width = "22px";
  marker.style.height = "22px";
  marker.style.border = "3px solid #ffffff";
  marker.style.borderRadius = "9999px";
  marker.style.background = "#146f94";
  marker.style.boxShadow = "0 10px 30px rgba(20, 111, 148, 0.36)";

  return marker;
}

function setMarker(
  map: MapboxMap,
  markerRef: MutableRefObject<Marker | null>,
  coordinates: Coordinates
) {
  const lngLat: [number, number] = [coordinates.longitude, coordinates.latitude];

  if (!markerRef.current) {
    markerRef.current = new mapboxgl.Marker({
      anchor: "center",
      element: createObservationMarkerElement()
    })
      .setLngLat(lngLat)
      .addTo(map);
    return;
  }

  markerRef.current.setLngLat(lngLat);
}

export function MontereyMap({
  className = "",
  error,
  id = "california-coast-map",
  onChange,
  value
}: MontereyMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const hasLoadedRef = useRef(false);
  const mapRef = useRef<MapboxMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const onChangeRef = useRef(onChange);
  const valueRef = useRef(value);
  const [mapStatus, setMapStatus] = useState<MapStatus>(
    MAPBOX_TOKEN ? "loading" : "error"
  );
  const [mapError, setMapError] = useState<string | null>(
    MAPBOX_TOKEN ? null : "Set VITE_MAPBOX_TOKEN to enable the California coast map."
  );

  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);

  useEffect(() => {
    valueRef.current = value;
  }, [value]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    if (!MAPBOX_TOKEN) {
      setMapStatus("error");
      setMapError("Set VITE_MAPBOX_TOKEN to enable the California coast map.");
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;
    setMapStatus("loading");
    setMapError(null);

    const map = new mapboxgl.Map({
      attributionControl: true,
      center: CALIFORNIA_COAST_CENTER,
      container: containerRef.current,
      dragRotate: false,
      maxBounds: CALIFORNIA_COAST_BOUNDS,
      maxZoom: MAX_ZOOM,
      minZoom: MIN_ZOOM,
      pitchWithRotate: false,
      style: document.documentElement.classList.contains("dark") ? NIGHT_STYLE : DAY_STYLE,
      zoom: INITIAL_ZOOM
    });

    map.touchZoomRotate.disableRotation();

    const handleLoad = () => {
      hasLoadedRef.current = true;
      setMapStatus("ready");
      map.resize();

      if (valueRef.current) {
        setMarker(map, markerRef, valueRef.current);
      }
    };

    const handleError = () => {
      if (!hasLoadedRef.current) {
        setMapStatus("error");
        setMapError(
          "Unable to load the California coast map. Check the Mapbox token and network connection."
        );
      }
    };

    const handleClick = (event: MapMouseEvent) => {
      const coordinates = {
        latitude: Number(event.lngLat.lat.toFixed(6)),
        longitude: Number(event.lngLat.lng.toFixed(6))
      };

      setMarker(map, markerRef, coordinates);
      onChangeRef.current(coordinates);
    };

    const handleThemeChange = (event: Event) => {
      const theme = (event as CustomEvent<"dark" | "light">).detail;
      map.setStyle(theme === "dark" ? NIGHT_STYLE : DAY_STYLE);
    };
    window.addEventListener("bluetrace-theme-change", handleThemeChange);

    map.on("load", handleLoad);
    map.on("error", handleError);
    map.on("click", handleClick);

    mapRef.current = map;

    return () => {
      window.removeEventListener("bluetrace-theme-change", handleThemeChange);
      map.off("load", handleLoad);
      map.off("error", handleError);
      map.off("click", handleClick);
      hasLoadedRef.current = false;
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!containerRef.current || typeof ResizeObserver === "undefined") {
      return;
    }

    const observer = new ResizeObserver(() => {
      mapRef.current?.resize();
    });
    observer.observe(containerRef.current);

    return () => {
      observer.disconnect();
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) {
      return;
    }

    if (!value) {
      markerRef.current?.remove();
      markerRef.current = null;
      return;
    }

    setMarker(mapRef.current, markerRef, value);
    mapRef.current.easeTo({
      center: [value.longitude, value.latitude],
      duration: 450
    });
  }, [value]);

  return (
    <div className={["space-y-4", className].filter(Boolean).join(" ")}>
      <div
        className="relative h-[22rem] min-h-[20rem] overflow-hidden rounded-2xl border border-research-line bg-ocean-50 shadow-inner sm:h-[26rem] lg:h-[30rem] dark:bg-slate-950"
        id={id}
      >
        <div
          aria-label="Interactive California coast observation site map"
          className={[
            "h-full w-full transition-opacity duration-300",
            mapStatus === "ready" ? "opacity-100" : "opacity-30"
          ].join(" ")}
          ref={containerRef}
        />

        {mapStatus === "loading" ? (
          <div
            aria-live="polite"
            className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-[2px]"
            role="status"
          >
            <div className="flex items-center gap-3 rounded-full border border-ocean-100 bg-white/92 px-4 py-3 text-sm font-medium text-research-muted shadow-sm">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-ocean-100 border-t-ocean-600" />
              Loading California coast map...
            </div>
          </div>
        ) : null}

        {mapStatus === "error" && mapError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-ocean-50/92 p-8 text-center">
            <p className="max-w-sm text-sm leading-6 text-research-muted">
              {mapError}
            </p>
          </div>
        ) : null}
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
          Click once within the California coast study area to select the observation
          site. Clicking again moves the existing marker and updates latitude and
          longitude.
        </p>
      )}

      {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}
    </div>
  );
}
