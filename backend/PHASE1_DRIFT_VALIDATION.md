# Phase 1 — Environmental data and exploratory backward drift

## Implemented

- Independent `POST /api/v1/drift/estimate` endpoint; the image analysis endpoint remains unchanged.
- Historical-window request based on **observation date and time**, not upload time.
- Current-only, fixed-location backward Euler displacement and chronological track points.
- Explicit unavailable status when marine data is missing or the anchor is too far from the requested observation time.
- Request validation for Monterey Bay coordinates and 1–72-hour tracing windows.
- Mocked tests for validation, historical dates, missing observations, and current direction.

## Example request

```json
{
  "date": "2026-10-23",
  "time": "09:43",
  "latitude": 36.92991,
  "longitude": -121.860591,
  "hours": 24
}
```

Use `POST http://127.0.0.1:8000/api/v1/drift/estimate`. A past observation is permitted even when the image is uploaded weeks later, **if** the provider can supply data for the requested window.

## Important scientific and operational limitations

This is an **experimental computational baseline**, not a validated marine-debris source locator. It samples currents only at the observation location and assumes the sampled direction convention is the direction of transport. It does not model spatially varying currents, windage, waves, tides, shoreline collisions, beaching, diffusion, uncertainty, or varying debris properties. Paths can cross land and should never be presented as proven sources.

The current Marine API endpoint may not cover older historical dates. The code intentionally reports `unavailable` rather than silently substituting today's conditions. A verified historical-ocean-current provider, unit/direction verification against provider metadata, and end-to-end live validation are required before claiming historical coverage.

Timezone is fixed to `America/Los_Angeles`; ambiguous local times at daylight-saving transitions are not yet disambiguated by the API. The nearest marine reading may precede the actual observation by up to 90 minutes; the response exposes the anchor time in the path.

The unit assumption for ocean-current velocity is km/h. **Verify this against the provider's `hourly_units` metadata before interpreting physical distances.** Automated tests currently mock provider responses and do not establish scientific validity.

## Run tests

From the repository's `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pip install tzdata
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Acceptance checklist before phase-1 scientific sign-off

- [x] Endpoint and request validation implemented
- [x] Historical observation date is preserved in pipeline
- [x] Missing historical data returns an unavailable status
- [x] Mocked tests for key error paths written
- [ ] Run all tests locally on Windows
- [ ] Verify current velocity units and direction convention with provider metadata
- [ ] Validate real provider coverage for an observation from one week ago
- [ ] Test coastline crossings and real Monterey Bay cases
- [ ] Quantify uncertainty and compare against independent drift observations

Weather API 429 resilience is intentionally deferred; the drift endpoint does not call the weather API.

## November 2026 follow-up

- Frontend now renders a separate Mapbox line for the backward drift track and labels the observation anchor and oldest calculated point.
- The API exposes `anchor_time` and `observation_offset_minutes`.
- Marine history reads provider `hourly_units` for current speed and direction and converts supported speed units to km/h.
- An ambiguous or nonexistent Los Angeles local time during a daylight-saving transition is rejected conservatively.
- An observation from October 21, 2026 returned 23 hours of an experimental 24-hour requested track in a live user test (prior to these changes).

**Outstanding:** Coastline intersection is not yet computationally verified; the displayed basemap is for human inspection, not a geographic land mask. The provider's directional convention has not been independently confirmed, and no reference trajectories have been used for scientific validation. Historical coverage outside the tested dates remains unverified. New code and tests require local execution.

## Coastline screening setup and scientific status

Install dependencies with `pip install -r requirements.txt` from backend.
Set `BLUETRACE_LAND_GEOJSON` to an **existing** WGS84 GeoJSON
FeatureCollection containing authoritative Monterey Bay land polygons.
For example, in PowerShell:
```powershell
$env:BLUETRACE_LAND_GEOJSON="D:\\data\\monterey-land.geojson"
```
No authoritative coastline data file is bundled. If the environment variable is
unset, the file is missing, or geometry cannot be loaded, the response is
`coastline_status: not_checked` and MUST NOT be interpreted as clear.
The screening intersects the entire polyline with polygonal land, not only
individual vertices. A `clear_on_reference_map` result depends on the
resolution and quality of the configured dataset.

**Direction verification:** Open-Meteo Marine Weather API documentation defines
`ocean_current_direction` as the direction **towards which** water flows:
0° north, 90° east. The backward integration correctly subtracts the north
and east components. This convention differs from wave direction (from which
waves originate). Source: https://open-meteo.com/en/docs/marine-weather-api

**Analytical verification:** Unit tests check zero-current displacement,
1 km/h northward for one hour (~0.008993° latitude backward), and eastward
currents moving backward west. These are synthetic reference cases, NOT
validation against observed debris drifter trajectories.

**Still needed before scientific closure:** supply and inspect authoritative
Monterey land polygons, verify live coastline status on sample trajectories,
run the new test suite, compare tracks against independent drifter/buoy
observations, and quantify uncertainty. Open-Meteo warns that coastal current
model accuracy is limited at its approximately 8 km resolution. Older dates
may require the provider's historical forecast mode.

## November 2, 2026 integration update

- The backend now defaults to `backend/data/monterey_land.geojson` when `BLUETRACE_LAND_GEOJSON` is unset; the environment variable still overrides the default. The GeoJSON is a **local runtime prerequisite**, not automatically downloaded or committed.
- The frontend map disclaimer now reflects `potential_land_crossing`, `clear_on_reference_map`, or `not_checked` rather than always claiming no coastline validation.
- A user-run Monterey Bay scenario on October 24, 2026 returned `potential_land_crossing` in the API and showed the corresponding UI warning. This verifies the end-to-end screening path for that scenario, not the geographic correctness of the coastline data or the physical accuracy of the drift.
- User previously reported 26/26 backend unit tests passing **before these latest edits**. Re-run backend tests and frontend build after pulling the branch.

### Phase-1 engineering versus scientific completion

Engineering acceptance: local dataset readable, both `potential_land_crossing` and `clear_on_reference_map` behavior tested, missing/bad data fails closed as `not_checked`, backend tests pass, frontend builds, and end-to-end API/UI smoke test passes after these changes.

Scientific acceptance remains **open**: compare predicted tracks with independent real drifter observations, measure error and uncertainty, and document the limits of fixed-location currents and nearshore model resolution. Do not label the output as verified debris source attribution.

### Local verification

From project root, pull `feat/marine-environment-data`. Confirm `backend/data/monterey_land.geojson` exists. From `backend` run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

From `frontend` run `npm run build` and open the app for a drift smoke test. No manual environment variable is required when the default GeoJSON file exists.
