# BlueTrace AI

**Experimental marine debris analysis and source-region research along the California coast.**

BlueTrace AI is a research-oriented platform exploring how **computer vision, environmental data, and geospatial analysis** can be combined to analyze marine debris and explore potential source regions. The current backward-drift calculation is an experimental baseline, not a trained origin-prediction model.

The California coast study area is an initial bounding box (32–42°N, 125–117°W), not a water-only mask. The system processes marine debris observations — including an image, geographic location, date, and time — through an analysis pipeline incorporating **YOLO-based object detection, environmental data, and location scoring**.

> **Status:** 🚧 Active development. The analysis pipeline is functional, with ongoing work on model validation and prediction quality.

## Features

* Marine debris image upload and validation
* Geographic observation capture with Mapbox
* Observation date and time recording
* YOLO-based object detection
* Environmental data integration
* Location classification and scoring
* REST API for analysis
* Modular frontend and backend architecture

## Architecture

```text
Observation
    │
    ├── Image
    ├── Date & Time
    └── Location
          │
          ▼
    React Frontend
          │
          ▼
     FastAPI API
          │
     ┌────┴────┐
     ▼         ▼
   YOLO    Environment
 Detection    Data
     │         │
     └────┬────┘
          ▼
   Location Scoring
          │
          ▼
    Location Scoring
```

## Tech Stack

**Frontend**

React · TypeScript · Vite · TailwindCSS · Framer Motion · React Hook Form · React Query · Axios · Mapbox GL JS

**Backend**

Python · FastAPI · Pydantic · Uvicorn

**AI & Data**

YOLO · Machine Learning · Geospatial Analysis · Environmental Data

## Project Structure

```text
BlueTrace AI/
├── frontend/
│   └── src/
│       ├── assets/
│       ├── components/
│       ├── hooks/
│       ├── layouts/
│       ├── pages/
│       ├── services/
│       ├── styles/
│       └── types/
│
├── backend/
│   └── app/
│       ├── core/
│       ├── routers/
│       ├── schemas/
│       ├── services/
│       └── utils/
│
└── .env.example
```

## Getting Started

### Environment Variables

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

Add the required environment variables, including the Mapbox access token.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

### Backend

```bash
cd backend
python -m venv .venv
```

**Windows:**

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

API documentation is available at:

`http://localhost:8000/docs`

## API

### `POST /api/v1/analyze`

Accepts a marine debris observation using `multipart/form-data`.

| Field       | Description           |
| ----------- | --------------------- |
| `image`     | Marine debris image   |
| `date`      | Observation date      |
| `time`      | Observation time      |
| `latitude`  | Observation latitude  |
| `longitude` | Observation longitude |

The endpoint processes the observation and returns the available environmental information, object detections, and prediction results.

## California coast migration and historical training data 

- API input bounds and Mapbox observation map now cover California coast rather than Monterey Bay.
- The existing local coastline file path remains `backend/data/monterey_land.geojson` for compatibility. It must contain California-wide or global WGS84 land polygons. A Monterey-only clipping is **not sufficient**. A missing/unreadable file produces `not_checked`, never a clear verdict. The land intersection test does not simulate beaching.
- NOAA hourly drifter trajectories are the candidate supervised-learning labels for a future 24-hour previous-position model; the model is **not implemented or trained** yet. The coastline migration does not change the existing YOLO model.
- Open-Meteo Historical Weather API (ERA5) has hourly weather reanalysis back to 1940, but the existing `WeatherService` uses the **Historical Forecast API** (approximately 2022 onward). For training with 1992–2022 drifters, use ERA5 archive rather than assuming the current service covers those years.
- Open-Meteo ERA5-Ocean is historical *wave reanalysis*, not a validated historical ocean-current source. The overlap probe found 24/24 hourly wind and wave values but 0/24 current velocity/direction values at every one of six sampled date/location combinations in 1992, 2011, and 2022. Do not fill those absent currents with zero or train on them as if observed. Run `python scripts/check_open_meteo_overlap.py` from `backend` to reproduce the checks.\n- Historical current candidate: Copernicus Marine GLORYS12V1 (`GLOBAL_MULTIYEAR_PHY_001_030`, 1993 onwards, daily eastward/northward sea-water velocity at ~1/12-degree). Another candidate is NASA OSCAR v2.0, daily surface currents from 1993 at ~0.25-degree. Daily resolution is **not** hourly; align it explicitly and evaluate its limitations for 24-hour origin estimates. Verify actual values and licensing/access for a California spatial/temporal sample before use.\n- NOAA 1992 drifter observations predate the cited 1993 current reanalysis: either omit them from the current-enhanced dataset or use a separately validated source.
- Before joining NOAA and Open-Meteo, align timestamps in UTC, account for the grid-cell mismatch, and split by drifter ID to prevent data leakage. Do not train from present-day marine values attached to old drifter observations. 

## Development Status

BlueTrace AI is an **active research and engineering project**. The current implementation includes the core observation workflow, YOLO-based detection, environmental-data integration, and an initial location-scoring pipeline.

Prediction quality and the underlying analysis methodology are still being validated and refined.

## License

This project is currently under development. Licensing terms will be added when finalized.
