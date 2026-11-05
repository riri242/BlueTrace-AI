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
    Experimental Location Scoring
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

## California coast migration and historical training data\n\n- API input bounds and Mapbox observation map now cover California coast rather than Monterey Bay.\n- The existing local coastline file path remains `backend/data/monterey_land.geojson` for compatibility. It must contain California-wide or global WGS84 land polygons. A Monterey-only clipping is **not sufficient**. A missing/unreadable file produces `not_checked`, never a clear verdict. The land intersection test does not simulate beaching.\n- NOAA hourly drifter trajectories are the candidate supervised-learning labels for a future 24-hour previous-position model; the model is **not implemented or trained** yet. The coastline migration does not change the existing YOLO model.\n- Open-Meteo Historical Weather API (ERA5) has hourly weather reanalysis back to 1940, but the existing `WeatherService` uses the **Historical Forecast API** (approximately 2022 onward). For training with 1992–2022 drifters, use ERA5 archive rather than assuming the current service covers those years.\n- Open-Meteo Marine documentation lists ERA5-Ocean back to 1940, but verify that the exact ocean-current variables are actually populated at the drifter dates/locations. Run `python scripts/check_open_meteo_overlap.py` from `backend` to sample 1992, 2011, and 2022 in GMT/UTC. The probe is not exhaustive and does not establish model quality.\n- Before joining NOAA and Open-Meteo, align timestamps in UTC, account for the grid-cell mismatch, and split by drifter ID to prevent data leakage. Do not train from present-day marine values attached to old drifter observations.\n\n## Development Status

BlueTrace AI is an **active research and engineering project**. The current implementation includes the core observation workflow, YOLO-based detection, environmental-data integration, and an initial location-scoring pipeline.

Prediction quality and the underlying analysis methodology are still being validated and refined.

## License

This project is currently under development. Licensing terms will be added when finalized.
