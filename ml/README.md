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
| Copernicus GLORYS12V1 | uo/vo sea-water velocity | **Daily mean** | 2011 pilot downloaded and sampled successfully (24/24) |
| Copernicus WAVERYS | VSDX/VSDY Stokes drift, VHM0 waves | **3-hourly instantaneous** | 2011 pilot downloaded and sampled successfully (24/24) |

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

## First environmental coverage pilot (recommended next action)

From `ml/`, after installing the `marine` extras and authenticating
Copernicus Marine:

```powershell
python scripts/build_pilot.py --noaa "data/raw/drifter_hourly_qc.csv" --year 2011 --sample-size 24
```

This chooses one compact ~3-day period containing valid NOAA 24-hour
backtracking labels, with up to 24 observations spread across drifters.
It downloads **small study-region/time subsets** for GLORYS and WAVERYS,
requests hourly ERA5 wind for sampled locations, and creates:

- `data/interim/pilot/environment_pilot.csv` — aligned predictors,
  source timestamps, grid locations and completeness flags.
- `data/interim/pilot/coverage_report.json` — usable coverage per source.
- `data/interim/pilot/marine/*.nc` — downloaded Copernicus subsets.

The script performs **up to 24 ERA5 network calls**, requires Internet and
Copernicus credentials, and can encounter API rate limits. It is a
**coverage pilot, not a full training dataset**. Check the report and any
unmatched records before launching larger historical downloads. Full
training requires more drifters and a tested multi-year extractor.

## Resumable multi-year coverage check

After the successful 24-row pilot, use the bounded multi-year builder.
From `ml/` with Copernicus Marine credentials:

```powershell
python scripts/build_dataset.py --list-years
python scripts/build_dataset.py --auto-years --sample-size 24
```

The builder lists the actual NOAA years with suitable compact windows.\n`--auto-years` picks three chronologically separated eligible years without\nguessing dates; explicit `--years 2011 ...` is also supported.\nThe builder prechecks that NOAA has suitable compact windows in all\nrequested years. For each year it downloads a small spatial/time slice of
GLORYS daily currents and WAVERYS 3-hour wave fields, plus point-specific
ERA5 winds. It saves source provenance and completeness information under
`data/interim/multiyear/batches/<year>/`, and combines complete feature rows
into `data/interim/multiyear/environment.csv`, with a summary
`coverage_report.json`.

Repeating the command reuses a completed batch only when its selected
NOAA ID/time/coordinates fingerprint matches. Use `--refresh` to
re-download. If an explicit year has no suitable NOAA compact window, the error lists\neligible years; no download occurs before year-window validation.

**Important:** Three small windows (72 observations total at most) assess
feasibility only; they do not produce an independently validated model.
The builder uses current-location environmental snapshots, not a
24-hour time-varying physics integration. Do not represent this as a
final training-ready dataset. The training-facing CSV may contain fewer
than six independent drifters and cannot automatically satisfy the
`train.py` split requirement.

## Diverse NOAA sampling — preview before downloading

The original multi-year pilot recovered 72 complete observations but only
five independent drifters. The diversity-focused selector can inspect more
distinct NOAA trajectories across separate compact time/space windows without
issuing any marine API requests:

```powershell
python scripts/build_diverse.py --years 2010 2011 2015 2021 2022
```

The default preview selects up to three windows per year and up to 12
observations per window (maximum 180 rows). It writes
`data/interim/diverse/selection_report.json` and prints the number of
distinct drifters, selected windows and records. Windows are restricted to
short time spans and spatial extents. The selector favors drifters not yet
selected. Examine `unique_drifters` and per-year breakdown **before**
issuing any downloads. A larger row count does not guarantee more
independent trajectories.

Only after reviewing the preview, run the same command with `--download`
to fetch Copernicus and ERA5 data. Completed individual batches are cached,
but individual API requests may still fail or be rate-limited. The resultant
environment.csv is an experimental snapshot table: no final inference or
debris-origin accuracy claim is justified from it.

## Model V2: robustness evaluation on the completed diverse dataset

After the 180-record, 63-drifter environmental extraction succeeded, run a
strict experimental robustness evaluation instead of interpreting one favorable
hold-out split as proof of generalization:

```powershell
python -m pytest -q
python -m bluetrace_ml.robustness \
  --noaa "data/raw/drifter_hourly_qc.csv" \
  --environment "data/interim/diverse/environment.csv" \
  --output "artifacts/hybrid_v2_evaluation"
```

The script repeats group-disjoint train/validation/test splits with five
different random seeds, then independently evaluates held-out whole years.
For year holdouts, every drifter seen in that year is excluded entirely from
training and validation—even if it was observed in another year. Each fold
compares Hybrid Physics–XGBoost, constant-current backtracking and
no-movement **on exactly the same test records**. Outputs are written
to `artifacts/hybrid_v2_evaluation/robustness.json`; the CLI prints aggregate
mean errors, variation and number of wins over the physics baseline.

Read the fold-level results, group sizes and held-out-year results. Do not
interpret the seed-level mean and standard deviation as confidence intervals:
the folds overlap. A year split with too few disjoint drifters is skipped;
report how many year tests were performed rather than assuming all five.
The resulting statistics are **exploratory**, not production-ready.
The script neither changes the existing `hybrid_v1` model nor deploys it.

The next experiment should extend the data beyond 180 observations and
integrate currents/wind/Stokes across the full preceding 24 hours. This V2
assessment does **not** implement a time-varying trajectory integrator.

## V3: 24-hour temporal environmental pilot (cached marine grids)

Before expanding downloads or changing the fitted model, inspect whether
historical marine grids and ERA5 contain 24 hourly-aligned predictors
at the observation location. The script reads the **already downloaded**
Copernicus grids from the `diverse` dataset directory; it will **not**
contact Copernicus again. It does call Open-Meteo once for each selected
observation (default **3 requests**) to obtain hourly historical winds:

```powershell
python -m pytest -q
python scripts/build_temporal.py --max-observations 3
```

The output `data/interim/temporal_pilot/temporal_pilot.csv` includes
per-channel mean and standard deviation, timestamp coverage and a simple
24-step constant-location current sum. `coverage_report.json` counts
observations with all six channels present for all 24 samples.

Matching uses the latest source grid timestamp at/before each target UTC
hour, with explicit source age tolerances and no grid timestamps after
the observation date. **This is not a promise of real-time
information availability.** The GLORYS daily-mean time label can
represent a retrospective whole-day aggregate, so it can contain
information from later that calendar day. For a strictly prospective
forecast or real-time deployment, use a timestamp-released operational
product or lag daily aggregates until their real availability time.
The pilot is explicitly **retrospective**, and uses a fixed observed
location rather than following an advected trajectory.

If the first three examples have good coverage, the next phase can
rework extraction for larger numbers of independently sampled drifters,
cache ERA5 requests, and build a spatially evolving 24h backtracking
integrator. This code does **not** fit a V3 model or replace `hybrid_v1`.

## V3 spatially evolving backward-trajectory pilot

The existing 3-observation temporal pilot reported full 24-hour
fixed-location predictor coverage. To test a **moving spatial trajectory**
without authenticating to Copernicus again, use cached GLORYS and WAVERYS
NetCDF files from the diverse extraction:

```powershell
python -m pytest -q
python scripts/trace_trajectory.py --max-observations 3
```

The new `bluetrace_ml.trajectory` module performs 24 one-hour backward
Euler steps. At each step it retrieves the latest timestamped ocean field
at or before that step, samples the nearest cell at the **updated** modeled
location, and subtracts the water velocity. It optionally adds WAVERYS
Stokes drift to the current, as an uncalibrated experiment. Missing values,
stale fields, exceeded spatial coverage and domain exits are **reported as
incomplete**, not silently extrapolated.

`data/interim/trajectory_pilot/comparison.csv` compares complete traces
to NOAA's actual 24h previous position, alongside a no-movement baseline.
`paths.json` records the hourly positions and field source labels.
`report.json` reports completion and preliminary mean error. Compare
errors only on a common set of completed traces; different success counts
make aggregate means misleading.

This pilot is **not Model V3 training** and does not modify saved
hybrid models. Cached grids were downloaded around observation locations
for narrow time spans; modeled trajectories may leave the cache and fail.
The daily GLORYS fields are retrospective time averages, not point-in-time
operational forecasts. Windage, wave-current coupling, coastline/land
collisions, stranding, spatial interpolation and uncertainty are not yet
modeled. Testing three drifters does not establish predictive accuracy.

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
