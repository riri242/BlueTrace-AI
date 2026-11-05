# BlueTrace AI — Marine Backtracking ML

Experimental, reproducible training workspace for a **24-hour previous-position
prediction** using NOAA Global Drifter Program quality-controlled hourly trajectories.

This is **not** yet a validated marine debris origin model. GDP drifters are
proxies for floating motion; debris size, buoyancy, windage, stranding and
nearshore dynamics can change trajectories substantially.

## Data suitability audit (California bbox)

Locally inspected NOAA CSV: **145,194 rows; 156 drifters; no missing core
columns; 137,739 complete 24-hour observation pairs from 151 drifters; 137,070
pairs with target timestamps in 1993 or later.** Dates are
1992-11-21–2022-10-23 (UTC). Pairs overlap heavily and are *not*
independent. The sampled 24-hour displacement had median about **12.3 km**
and p90 about **28.2 km**. Bounding-box clipping and variable coastal
coverage limit generalization.

### Historical predictor sources

| Source | Variables | Cadence | Availability status |
| --- | --- | --- | --- |
| NOAA GDP | ID, UTC time, coordinates; ve/vn excluded from inference features | Hourly | Actual CSV audited |
| Open-Meteo ERA5 Archive | 10 m wind speed/direction | Hourly | Six historical API samples returned valid winds |
| Copernicus GLORYS12V1 | uo/vo sea-water velocity | **Daily mean** | Metadata verified; actual sample **not yet downloaded** |
| Copernicus WAVERYS | VSDX/VSDY Stokes drift, VHM0 waves | **3-hourly instantaneous** | Metadata verified; actual sample **not yet downloaded** |

**Do not call WAVERYS hourly or GLORYS hourly.** Avoid joining daily/3-hourly
fields as if they were hourly independent measurements. Both sampled grid
locations and source timestamps must be recorded. The available-data-at-
inference constraint must be checked, especially if doing a real-time service.

GLORYS begins 1993, so 1992 NOAA records cannot be included in the complete
environmental training set without a different historical current source.
Open-Meteo's current Marine service does not supply currents for our old dates.

## Install

Run from `ml/` with Python 3.10–3.13:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q
```

The ML virtual environment can be separate from the FastAPI environment
to avoid unnecessary runtime dependencies.

## Audit and train the honest baseline

```powershell
python -m bluetrace_ml.audit --noaa "data/raw/drifter_hourly_qc.csv"
python -m bluetrace_ml.train --noaa "data/raw/drifter_hourly_qc.csv" --output "artifacts/location_only"
```

Place the NOAA file downloaded earlier at `ml/data/raw/drifter_hourly_qc.csv`.
The loader detects ERDDAP's unit row, parses timestamps in UTC, validates the
geometry and builds only **uninterrupted** 24-hour trajectories.

The resulting `evaluation.json` compares:
- no movement (persistence);
- mean displacement learned on training drifters only;
- a location/time-only XGBoost regression with two outputs, east/north offsets.

**Location/time-only XGBoost is a sanity-check prototype, not a physics model
and not suitable for deploying a source estimate.** It does not observe ocean
currents and can be outperformed by basic physics. It is never marked
`production_ready`. Each split uses separate drifter IDs, with km error
statistics (mean / median / p90) and an explicit model feature list.

## Verify Copernicus access before building the environment feature dataset

Create a Copernicus Marine account if needed, then from `ml/`:

```powershell
python -m pip install -e ".[dev,marine]"
python scripts/probe_copernicus.py --start 2011-03-25 --end 2011-03-27 --latitude 36.8 --longitude -122.0
```

The probe requests only a 1° sample for each product, prints dimensions,
units and counts of actual non-null values. Access can require Copernicus
authentication. **Successful metadata lookup does not prove usable ocean
cells at every drifter point.** The outputs live in ignored `data/raw/probes/`.

## Environmental join contract (future training)

A separate extractor must generate `environment.csv` with **one row per
NOAA ID + exact UTC observation timestamp**, including:
`ID,time,sample_latitude,sample_longitude,wind_u,wind_v,current_u,current_v,
stokes_u,stokes_v`.

- Values must use east/north **m/s** and be extracted from a documented
  source grid/timestamp at that observation's location.
- For GLORYS, use the daily mean from a matching day; for WAVERYS, use a
  documented nearby 3-hour instant; for ERA5, use hourly wind.
- Record source timestamps, grids, interpolation policy, masks, and provenance
  in a separate manifest before treating the combined table as validated.
- The strict join rejects missing measurements or mismatching positions
  instead of treating absent currents as zero.
- A point-snapshot of environment is a first experiment; full 24-hour
  backward integration or temporal feature summaries require another
  pipeline and must not be misrepresented as already implemented.

After building and validating the feature table:

```powershell
python -m bluetrace_ml.train --noaa "data/raw/drifter_hourly_qc.csv" --environment "data/processed/environment.csv" --output "artifacts/environmental"
```

When environmental training is enabled, the target becomes the **residual**\nbetween observed 24-hour displacement and a constant-current backtracking\nbaseline. XGBoost learns this residual; test reports compare the raw\nconstant-current estimate and the hybrid estimate. This simple current\nbaseline holds daily current fixed for 24 hours and is **not** a full\nLagrangian simulation. The environment feature table is **not generated\nor validated yet**. Offline inference lives in `bluetrace_ml.predict`.

## Next research milestones

1. Verify Copernicus data access at real NOAA times/locations and quantify
   missing coastal pixels, spatial and temporal offsets.
2. Build reproducible, chunked historical weather/current/wave extraction
   with a provenance manifest, and train on valid overlap only.
3. Add a separate physics-only 24-hour reverse-current baseline, then train
   XGBoost residual correction and compare against persistence.
4. Test held-out geographic sectors/years, evaluate calibration/uncertainty,
   and only then decide if the model is ready to serve via FastAPI.

Source references:
- https://erddap.aoml.noaa.gov/gdp/erddap/tabledap/drifter_hourly_qc.html
- https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_PHY_001_030/services
- https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_WAV_001_032/services
- https://open-meteo.com/en/docs/historical-weather-api
