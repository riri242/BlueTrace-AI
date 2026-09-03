# BlueTrace AI

**AI-powered marine debris analysis and origin estimation.**

BlueTrace AI is a research-oriented platform exploring how **computer vision, environmental data, and geospatial analysis** can be combined to analyze marine debris and estimate potential origins.

The system processes marine debris observations — including an image, geographic location, date, and time — through an analysis pipeline incorporating **YOLO-based object detection, environmental data, and location scoring**.

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
    Origin Estimate
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

## Development Status

BlueTrace AI is an **active research and engineering project**. The current implementation includes the core observation workflow, YOLO-based detection, environmental-data integration, and an initial location-scoring pipeline.

Prediction quality and the underlying analysis methodology are still being validated and refined.

## License

This project is currently under development. Licensing terms will be added when finalized.
