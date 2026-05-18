# Litterbox Repository Specification

## Project Overview

Litterbox is a cat health monitoring system for a Viervoeter/Tuya-connected litterbox. It consists of:

- A Python FastAPI backend that monitors device state, detects visits and cleaning cycles, identifies cats by weight, and stores historical data.
- A React/Vite frontend that displays dashboard summaries, visit history, cat management, and weight charts.
- Two runtime modes: `polling` and `webhook`.

This document describes the current architecture, API contract, persistence model, configuration, and operational behavior.

---

## Backend Architecture

### Core responsibilities

- Polls Tuya Cloud for device data in `polling` mode.
- Receives Tuya webhook events in `webhook` mode.
- Detects litterbox visits from weight readings.
- Detects cleaning cycles and device setting changes.
- Matches visits to active cats using reference weight thresholds.
- Stores visits, cats, cleaning cycles, device snapshots, and settings history in the database.
- Serves the frontend static build when `frontend/dist` exists.

### Entry point

- `app/main.py`
  - Creates the FastAPI application.
  - Uses `UPDATE_MODE` to decide whether to start a background poller thread or register a webhook poller.
  - Includes routers for cats, visits, cleaning cycles, and dashboard.
  - Serves `/uploads` cat photo assets with path checks and safe response headers.
  - Serves frontend assets from `frontend/dist` when present.

### Poller behavior

- `app/poller.py` defines `LitterboxPoller`.
- In `polling` mode:
  - `run_poller()` loops and calls `poll()` every 300 seconds.
  - The 5-minute interval is hardcoded to stay comfortably within Tuya API quotas.
  - `make_cloud()` initializes a `tinytuya.Cloud` client with `TUYA_API_KEY`, `TUYA_API_SECRET`, `TUYA_API_REGION`, and `TUYA_DEVICE_ID`.
  - The latest DP state is fetched via `cloud.getstatus(DEVICE_ID)`.
- In `webhook` mode:
  - No active polling thread is started.
  - `app.state.webhook_poller` is created and used by the webhook router.

### Visit detection

- Uses DP codes from Tuya:
  - `cat_weight`
  - `excretion_times_day`
  - `excretion_time_day`
  - `smart_clean`
- Visit start is triggered when `cat_weight` changes to a nonzero value.
- Visit completion is triggered when `excretion_times_day` changes.
- If status polling misses a short completion event, timeout handling first reconciles Tuya status report logs from `/v2.0/cloud/thing/{device_id}/report-logs` for `excretion_times_day`, `excretion_time_day`, and `cat_weight`.
- Fallback timeout closes an active visit if no status or report-log completion event is found within `VISIT_TIMEOUT_SECONDS` (300 seconds).
- Weight is stored in kilograms after converting from grams.

### Cat identification logic

- `app/cat_identifier.py` provides `identify_cat()` and `update_reference_weight()`.
- Identification uses a maximum deviation threshold of `0.5 kg`.
- A visit is auto-identified only when exactly one active cat is plausible for the observed weight.
- Identification is attempted when the first nonzero visit weight is seen, so clear in-progress visits can appear under the matched cat before duration completion.
- If no reference-weight match exists, the poller can use recent identified visit weights as a conservative fallback when exactly one cat clearly matches.
- On a successful auto-identification, the cat's `reference_weight_kg` is updated by a smoothing factor of `0.1` when the visit closes.

### Cleaning cycles and settings

- `smart_clean` DP changes start and end `CleaningCycle` records.
- Predefined litterbox setting DPs are saved into `SettingsHistory` when they change.
- Device snapshots are periodically saved to `DeviceSnapshot` every `SNAPSHOT_INTERVAL_SECONDS`.

---

## API Contract

### Health

- `GET /health`
  - Returns `{"status": "ok"}`.

### Dashboard

- `GET /dashboard`
  - Returns aggregated dashboard data for active cats, unidentified visits, cleaning cycles, and poller health.
  - Includes `poller_last_successful_at`, `poller_last_attempted_at`, and `poller_last_error` diagnostics.
  - In `webhook` mode, `poller_healthy` is always `true`.

### Display

- `GET /display/summary`
  - Returns compact JSON for an ESP32 4.2 inch black/white/red e-paper status display.
  - Includes poller status, latest visit, today's totals, compact per-cat summaries, optional alert text, and an optional 30-day weight chart.
  - Uses `refresh_after_seconds` so firmware can avoid refreshing faster than the backend recommends.

### Cats

- `POST /cats`
  - Creates a new cat.
  - Request body: `name`, optional `reference_weight_kg`.
  - Response: `CatOut`.

- `GET /cats`
  - Lists cats.
  - Supports `include_inactive` query parameter.

- `GET /cats/{cat_id}`
  - Returns a single cat.

- `PATCH /cats/{cat_id}`
  - Updates cat fields: `name`, `active`, `reference_weight_kg`.

- `POST /cats/{cat_id}/photo`
  - Uploads a cat photo as a base64 data URL.
  - Stores the image in `uploads/cat_photos/{cat_id}.{ext}` after server-side size and image-signature validation.

- `DELETE /cats/{cat_id}/photo`
  - Deletes the stored cat photo.

### Visits

- `POST /visits`
  - Creates a manual visit.
  - Request body: `cat_id`, `started_at`, `duration_seconds`, `weight_kg`.
  - Sets `ended_at` from `started_at + duration_seconds`.

- `GET /visits`
  - Lists visits.
  - Supports `limit`, `offset`, `cat_id`, and `unidentified` filters.

- `GET /visits/weight-history`
  - Returns per-cat weight history points for charting.
  - Supports `from_date`, `to_date`, and `cat_id` filters.

- `GET /visits/{visit_id}`
  - Returns a single visit.

- `PATCH /visits/{visit_id}`
  - Updates visit metadata.
  - Manual `cat_id` changes set `identified_by` to `manual`.

- `DELETE /visits/{visit_id}`
  - Deletes a visit record.

### Cleaning cycles

- `GET /cleaning-cycles`
  - Lists recent cleaning cycles.
  - Supports `limit`.

### Webhook mode

- `POST /webhook/tuya`
  - Accepts Tuya Message Subscription payloads.
  - Request body includes `dataId`, `devId`, optional `productKey`, and `status` list.
  - If `WEBHOOK_SECRET` is set, requires `X-Webhook-Secret` header.
  - Filters payloads by `TUYA_DEVICE_ID`.
  - Applies changed DPs to the webhook poller.

---

## Persistence Model

### Database engine

- `app/database.py` uses `DATABASE_URL`.
- The backend supports PostgreSQL in production and SQLite in tests.
- `get_db()` yields a SQLAlchemy session per request.

### Models

- `Cat`
  - `id`, `name`, `active`, `reference_weight_kg`, `photo_path`, `created_at`.

- `Visit`
  - `id`, `cat_id`, `identified_by`, `started_at`, `ended_at`, `duration_seconds`, `weight_kg`, `last_weight_at`, `created_at`.

- `CleaningCycle`
  - `id`, `started_at`, `ended_at`.

- `DeviceSnapshot`
  - `id`, `recorded_at`, `raw_dps`.

- `SettingsHistory`
  - `id`, `dp`, `value`, `changed_at`.

- `TZDateTime`
  - Custom SQLAlchemy type ensuring UTC-aware datetimes across PostgreSQL and SQLite.

---

## Frontend Architecture

### Overall structure

- `frontend/src/App.jsx`
  - React app shell with client-side routing.
  - Sidebar navigation for Dashboard, Visits, and Cats.
  - Dark mode persisted in `localStorage`.

- Uses React Router and lazy-loaded page components.
- Uses a toast provider for transient notifications.

### Pages

- `frontend/src/pages/Dashboard.jsx`
  - Displays active cat summaries, recent visits, poller status, and charts.

- `frontend/src/pages/Visits.jsx`
  - Displays visit history with filters and manual visit management.

- `frontend/src/pages/Cats.jsx`
  - Displays cat list and allows creating/updating cats and managing photos.

### Components

- `CatCard.jsx`
- `CatPhotoUpload.jsx`
- `PollerStatus.jsx`
- `Toast.jsx`
- `VisitsList.jsx`
- `WeightChart.jsx`

### API client

- `frontend/src/api/client.js`
  - Uses Axios with `VITE_API_URL`.
  - Wraps backend endpoints for dashboard, cats, visits, weight history, photo uploads, and cleaning cycles.

---

## Runtime Configuration

### Supported environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | SQLAlchemy database URL. Required. |
| `UPDATE_MODE` | `polling` | `polling` or `webhook`. |
| `SNAPSHOT_INTERVAL_SECONDS` | `300` | Device snapshot interval in seconds. |
| `UPLOADS_DIR` | `uploads` | Directory used for uploaded cat photos. |
| `MAX_CAT_PHOTO_BYTES` | `2097152` | Maximum decoded cat photo upload size in bytes. |
| `TUYA_DEVICE_ID` | — | Device ID used for polling and webhook filtering. |
| `TUYA_API_KEY` | — | Required in polling mode. |
| `TUYA_API_SECRET` | — | Required in polling mode. |
| `TUYA_API_REGION` | `eu` | Tuya cloud region: `eu`, `us`, `cn`, `in`. |
| `WEBHOOK_SECRET` | — | If set, required by `X-Webhook-Secret` on webhook requests. |

### Modes of operation

#### Polling mode

- Default mode: `UPDATE_MODE=polling`.
- Starts a background thread in `app/main.py`.
- Requires Tuya cloud credentials.
- Polls every 300 seconds and marks dashboard polling health stale after 900 seconds without a successful poll.
- Dashboard health is based on last successful poll.

#### Webhook mode

- `UPDATE_MODE=webhook`.
- No background poller thread.
- The `/webhook/tuya` route is enabled.
- Tuya API credentials are not required at runtime.
- Dashboard health is always `true` as long as the app is running.

---

## Testing and Validation

### Backend tests

- `python3 -m pytest tests/ -v`
- Test suite uses an in-memory SQLite DB and mocked Tuya access.
- Notable tests:
  - `tests/test_cat_identifier.py`
  - `tests/test_health.py`
  - `tests/test_api_cats.py`
  - `tests/test_api_visits.py`
  - `tests/test_api_cleaning_cycles.py`
  - `tests/test_api_dashboard.py`
  - `tests/test_api_display.py`
  - `tests/test_poller.py`

### Frontend tests

- `cd frontend && npm run lint`
- `cd frontend && npm test`
- Current Vitest coverage includes selected pages and components, including Visits, Cats, and Toast behavior.

---

## Important Behavior Notes

- The backend stores uploaded cat photos under `uploads/cat_photos/` and serves them from `/uploads/`.
- In webhook mode, the app constructs the full current DP state by merging webhook changes into the last known DP snapshot.
- Visit identification uses the latest weight reading and only matches cats within `0.5 kg` of their reference weight.
- Visits can be manually corrected through the `PATCH /visits/{visit_id}` endpoint.
- The frontend expects the backend API to be available at `VITE_API_URL` or the same origin if unset.

---

## Future extension points

- Add explicit webhook health and event audit logs.
- Support multiple devices or multiple litterboxes.
- Expand frontend component and page test coverage.
- Add end-to-end integration testing for webhook and polling modes.
