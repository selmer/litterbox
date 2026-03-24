# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Litterbox is a cat health monitoring system for a Viervoeter smart litterbox. It polls a Tuya IoT device for weight readings, identifies which cat visited using weight-based matching, and stores visits/cleaning cycles in PostgreSQL. A React frontend provides a dashboard and history views.

## Commands

### Backend
```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v            # all tests
python3 -m pytest tests/test_poller.py -v  # single test file
uvicorn app.main:app --reload          # dev server (requires DB)
alembic upgrade head                   # run migrations
alembic revision --autogenerate -m "description"  # new migration
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # Vite dev server with HMR
npm run build     # production build
npm run lint      # ESLint
npm run test      # Vitest
npm run test:watch
```

### Docker
```bash
docker compose up -d db                # start only the DB (for local backend dev)
docker compose up --build -d           # full stack
./deploy.sh                            # run tests → build → push → SSH deploy to NAS
```

## Architecture

### Data Flow

1. **LitterboxPoller** (`app/poller.py`) runs in a background thread, polling Tuya Cloud every `POLL_INTERVAL_SECONDS` (default 5s).
2. Weight changes trigger **visit start**; the `excretion_times_day` counter incrementing triggers **visit end**.
3. At visit end, `identify_cat()` (`app/cat_identifier.py`) matches weight against active cats using ±0.5kg threshold. Reference weights are updated via exponential moving average (α=0.1).
4. Results are written to PostgreSQL via SQLAlchemy. The poller opens a **fresh DB session per poll cycle** to avoid stale identity-map state.
5. FastAPI routers serve REST endpoints; the built React frontend is served as static files from the same process.

### Key Files

| Path | Role |
|------|------|
| `app/main.py` | FastAPI app, lifespan hook that starts the poller thread, static file serving |
| `app/poller.py` | `LitterboxPoller` class — all device polling, visit detection, cleaning cycle detection, settings change tracking |
| `app/cat_identifier.py` | Pure functions: `identify_cat()` and `update_reference_weight()` |
| `app/models.py` | SQLAlchemy models: `Cat`, `Visit`, `CleaningCycle`, `DeviceSnapshot`, `SettingsHistory` |
| `app/schemas.py` | Pydantic request/response schemas |
| `app/database.py` | Engine + `SessionLocal` factory |
| `app/routers/dashboard.py` | Aggregated today's stats + poller health |
| `conftest.py` | pytest fixtures — in-memory SQLite DB, mocked Tuya connection, patched poller thread |

### Database

PostgreSQL 16 in production, SQLite in tests. A custom `TZDateTime` SQLAlchemy type in `app/models.py` ensures UTC-aware datetimes work across both backends. Migrations are managed with Alembic (`alembic/versions/`).

### Frontend

React 19 + Vite. Three pages (Dashboard, Visits, Cats) routed via React Router. All API calls go through `src/api/client.js` (Axios wrapper). Charts use Recharts.

## Test Setup

Tests use an in-memory SQLite database and mock the Tuya cloud client — no real credentials or device needed. The `conftest.py` at the repo root patches `run_poller()` so the background thread doesn't start during tests.

## Environment Variables

See `.env.example`. Required at runtime: `DATABASE_URL`, `TUYA_DEVICE_ID`, `TUYA_DEVICE_IP`, `TUYA_API_KEY`, `TUYA_API_SECRET`, `TUYA_API_REGION`.
