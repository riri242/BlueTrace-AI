# BlueTrace AI Backend

FastAPI service for the BlueTrace AI Milestone 1 intake API.

This backend currently validates multipart analysis submissions only. It does not run AI, object detection, machine learning, or dataset ingestion.

## Requirements

- Python 3.13 or compatible Python 3 version
- A project-local virtual environment at `.venv`
- Dependencies installed from `requirements.txt`

## Create Virtual Environment

From the `backend` directory:

```powershell
python -m venv .venv
```

If Windows blocks `ensurepip` while creating the venv, rerun from a terminal with permission to write temporary files, then continue with the commands below.

## Activate Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.\.venv\Scripts\activate.bat
```

## Install Dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The dependency file is pinned for reproducible backend setup and includes FastAPI, Uvicorn, Pydantic, Pydantic Settings, python-dotenv, python-multipart, Supabase, httpx, and resolved runtime dependencies.

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

```powershell
Copy-Item .env.example .env
```

Required variables:

- `PORT`: Local backend port. Milestone 1.1 verification uses `8001`.
- `SUPABASE_URL`: Placeholder for future Supabase integration.
- `SUPABASE_ANON_KEY`: Placeholder for future browser-safe Supabase access.
- `SUPABASE_SERVICE_ROLE_KEY`: Placeholder for future trusted backend-only Supabase access. Never commit a real service-role key.

## Run Backend

From the `backend` directory with the virtual environment activated:

```powershell
uvicorn app.main:app --reload --port 8001
```

Equivalent venv-explicit command:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Backend URL:

```text
http://127.0.0.1:8001
```

Swagger UI:

```text
http://127.0.0.1:8001/docs
```

Health check:

```text
http://127.0.0.1:8001/health
```

## Common Troubleshooting

`ModuleNotFoundError: No module named 'pydantic_settings'`

The backend is running outside the project virtual environment or dependencies were not installed. Activate `.venv` and run `python -m pip install -r requirements.txt`.

`Form data requires "python-multipart" to be installed`

Install dependencies from `requirements.txt`; the package is pinned as `python-multipart`.

`uvicorn is not recognized`

Activate `.venv`, or run `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001`.

`Address already in use`

Another backend process is using the port. Stop that process or run with a different `--port`.

`Swagger UI does not load`

Confirm the backend process is running, then open `http://127.0.0.1:8001/docs`.

