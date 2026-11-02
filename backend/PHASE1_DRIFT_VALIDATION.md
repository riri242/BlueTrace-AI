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
