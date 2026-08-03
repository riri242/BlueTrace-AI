# BlueTrace AI

BlueTrace AI is a production-oriented research foundation for future marine debris origin estimation. Milestone 1 establishes the full-stack intake workflow only: image upload, observation date and time, Monterey Bay location capture, request validation, and API integration.

No AI, machine learning, object detection, datasets, or simulated inference are implemented in this milestone.

## Architecture

The project is split into independent frontend and backend applications.

```text
BlueTrace AI/
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   └── types/
│   └── ...
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   └── ...
└── .env.example
```

## Tech Stack

Frontend: React, Vite, TypeScript, TailwindCSS, Framer Motion, React Hook Form, React Query, Axios, and Mapbox GL JS.

Backend: FastAPI, Python, Pydantic, and Uvicorn.

## Installation

Copy the example environment files and add your Mapbox token:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
cp backend/.env.example backend/.env
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Install backend dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run Frontend

```bash
cd frontend
npm run dev
```

The Vite app runs at `http://localhost:5173`.

## Run Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The API runs at `http://localhost:8000`.

## API

`POST /api/v1/analyze`

Accepts `multipart/form-data`:

- `image`
- `date`
- `time`
- `latitude`
- `longitude`

Returns:

```json
{
  "status": "success",
  "message": "Milestone 1 completed.",
  "received": {
    "date": "2026-08-03",
    "time": "12:30",
    "latitude": 36.8,
    "longitude": -121.95,
    "image": {
      "filename": "sample.jpg",
      "content_type": "image/jpeg",
      "size_bytes": 123456
    }
  }
}
```

## Future Milestones

- Computer vision model experimentation and evaluation.
- Ocean current, tide, weather, and wind data ingestion.
- Research data storage and provenance tracking.
- Model training pipelines and reproducible experiments.
- Explainable origin estimation and uncertainty reporting.
- Field-ready analyst dashboards and export workflows.

