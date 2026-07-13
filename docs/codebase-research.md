# Codebase Research

Generated on 2026-07-13 from source code, tests, build configuration, deployment configuration, and existing documentation. Source, tests, and runtime configuration were treated as stronger evidence than prose docs.

## System Purpose and User-Facing Capabilities

Litterbox is a self-hosted cat health and litterbox activity monitor for a Tuya-connected automatic litterbox. The backend collects Tuya device state, derives visits and cleaning cycles, stores history, and exposes REST APIs. The frontend presents a household dashboard, visit history, cat profiles, lifecycle events, diagnostics, backup/restore, language/theme preferences, and Tuya configuration management.

Main capabilities verified in code:

- Dashboard summaries for active cats, visits today, trusted time in box, latest weight, unidentified visits, cleaning cycles, poller health, health signals, and device faults in `app/routers/dashboard.py` and `frontend/src/pages/Dashboard.jsx`.
- Cat management, active/inactive state, reference weights, birthdays, photo upload/delete, and shared lifecycle events in `app/routers/cats.py`, `frontend/src/pages/Cats.jsx`, and `frontend/src/pages/CatDetail.jsx`.
- Visit history, manual visit creation, editing, deletion, aggregate summaries by day/week/month, diagnostics per visit, and weight history in `app/routers/visits.py` and `frontend/src/pages/Visits.jsx`.
- Tuya device polling and webhook ingestion for weight, excretion counters/duration, cleaning cycles, setting changes, snapshots, device fault bits, and report-log reconciliation in `app/poller.py` and `app/routers/webhook.py`.
- Admin backup/restore and Tuya credential management in `app/routers/admin.py` and `frontend/src/pages/Admin.jsx`.
- Compact display API for ESP32 e-paper firmware via `GET /display/summary` in `app/routers/display.py` and `firmware/epaper-display/src/main.cpp`.
- Diagnostics summary including poller health, open visits, redacted recent diagnostic payloads, reconciliation counters, display payload, and useful endpoint links in `app/routers/diagnostics.py`.

## Repository and Module Structure

- `app/`: FastAPI backend.
  - `app/main.py`: application construction, lifespan startup, router inclusion, upload/static serving.
  - `app/routers/`: HTTP resources split by domain: `admin`, `cats`, `visits`, `cleaning_cycles`, `dashboard`, `display`, `diagnostics`, and conditional `webhook`.
  - `app/models.py`: SQLAlchemy ORM models and shared `Base`.
  - `app/schemas.py`: Pydantic request/response contracts and validation.
  - `app/database.py`: SQLAlchemy engine/session dependency from `DATABASE_URL`.
  - `app/poller.py`, `app/poller_runtime.py`, `app/cat_identifier.py`: Tuya ingestion, active poller reload hook, and cat matching logic.
  - `app/health_signals.py`, `app/device_faults.py`, `app/durations.py`, `app/timezones.py`: domain helpers used by routers and poller.
- `frontend/`: Vite/React frontend.
  - `frontend/src/App.jsx`: shell, lazy page routes, navigation, and theme state.
  - `frontend/src/api/client.js`: Axios API client.
  - `frontend/src/pages/`: Dashboard, Visits, Cats, CatDetail, Diagnostics, Admin.
  - `frontend/src/components/`: shared UI, charts, visit list, cat cards, upload, toasts.
  - `frontend/src/i18n/`: English/Dutch translations and browser language persistence.
- `tests/`: backend pytest suite using FastAPI `TestClient`, in-memory SQLite, and mocked Tuya.
- `frontend/src/**/*.test.jsx`: frontend Vitest and Testing Library tests beside app code.
- `alembic/`: database migrations. Current model metadata is imported by `alembic/env.py`.
- `firmware/epaper-display/`: PlatformIO Arduino firmware for an ESP32 e-paper display.
- `docs/`: operational docs, specs, archive, security audit note, and this research document.
- `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `requirements.txt`, `frontend/package.json`: runtime, deployment, and dependency definitions.

Untracked workspace directories currently exist: `.agents/`, `.github/`, and `.specify/` (`git status --short`). They appear to be local/spec tooling artifacts rather than tracked production app code.

## Entry Points and Execution Flows

Backend process:

- `app/main.py` creates `FastAPI(title="Litterbox API")`, installs permissive CORS and gzip middleware, includes API routers, exposes `/health`, serves `/uploads/{path:path}`, and serves `frontend/dist` if present (`app/main.py:88-145`).
- Startup uses `UPDATE_MODE`, defaulting to `polling`, and rejects any value other than `polling` or `webhook` (`app/main.py:22-24`).
- On startup, environment Tuya settings are seeded into `app_settings` if missing (`app/main.py:56-71`, `app/settings.py:62-74`).
- In polling mode, a daemon thread repeatedly calls `LitterboxPoller.poll()`, updates dashboard poll state, and sleeps for either 300 seconds or an adaptive delay (`app/main.py:29-53`, `app/poller.py:170+`).
- In webhook mode, no background polling thread is started. `app.state.webhook_poller` is created and the webhook router is included (`app/main.py:76-109`).

Tuya ingestion flow:

- `LitterboxPoller` initializes `tinytuya.Cloud` from resolved config and primes `previous_dps` with `cloud.getstatus()` (`app/poller.py:59-68`, `app/poller.py:107-125`).
- Each poll opens a fresh DB session, fetches current DPs, processes changes, checks visit timeout/reconciliation, snapshots state, and closes the session (`app/poller.py:170+`).
- A nonzero `cat_weight` starts or updates a visit and records a `weight_seen` diagnostic (`app/poller.py:801-837`).
- `excretion_times_day` or `excretion_time_day` can complete a visit from status DPs (`app/poller.py:424-467`).
- If completion is missed, timeout handling first tries Tuya report logs, then leaves the visit open until hard timeout, then closes with untrusted `hard_timeout` and `duration_seconds=None` (`app/poller.py:469-560`).
- `smart_clean` toggles cleaning cycle start/end, configured setting DPs create `SettingsHistory`, and periodic snapshots create `DeviceSnapshot` (`app/poller.py:1054-1082`).

Frontend flow:

- `frontend/src/main.jsx` renders `<App />`.
- `frontend/src/App.jsx` wraps the app in React Router, language provider, and toast provider, then lazy-loads Dashboard, Visits, Cats, CatDetail, Diagnostics, and Admin routes.
- `frontend/src/api/client.js` uses Axios with `VITE_API_URL` or same-origin base URL, matching the backend serving built assets and API from the same FastAPI process.

Firmware flow:

- The ESP32 firmware connects to Wi-Fi, fetches `DISPLAY_SUMMARY_URL`, parses JSON with ArduinoJson, renders the e-paper layout, and uses `refresh_after_seconds` from the backend for delay behavior (`firmware/epaper-display/src/main.cpp`).

## Languages, Frameworks, and Dependency Management

- Backend: Python 3, FastAPI, Starlette, SQLAlchemy 2, Alembic, Pydantic v2, Uvicorn, Tinytuya, psycopg2, pytest/httpx (`requirements.txt`).
- Frontend: JavaScript ES modules, React 19, React Router 7, Vite 8, Axios, Recharts, date-fns, Vitest, Testing Library, ESLint flat config (`frontend/package.json`, `frontend/vite.config.js`, `frontend/eslint.config.js`).
- Firmware: C++/Arduino for ESP32 through PlatformIO, with ArduinoJson, GxEPD2, and Adafruit GFX (`firmware/epaper-display/platformio.ini`).
- Backend dependencies are pinned or semi-pinned in `requirements.txt`; frontend dependencies are managed by `package.json` and locked in `frontend/package-lock.json`.

## Architectural Boundaries and Dependency Direction

- Routers depend on `app.database.get_db`, ORM models, Pydantic schemas, and small domain helpers. They do not call frontend code.
- The poller depends on settings, models, cat identification, device fault decoding, and imports dashboard router state to publish runtime health/fault information (`app/poller.py:10-13`, `app/poller.py:340+`).
- `app/settings.py` owns Tuya config resolution. The dependency direction is environment/DB settings -> poller/admin, not the reverse.
- `app/poller_runtime.py` is a small global active-poller registry used by Admin to reload Tuya credentials without restarting.
- Frontend depends only on HTTP APIs exposed through `frontend/src/api/client.js`; no frontend module imports backend code.
- Firmware depends on the stable JSON contract of `/display/summary`; it has no direct DB or Tuya dependency.
- Database models are the persistence boundary. Alembic reads `Base.metadata`, and Admin backup/restore iterates `Base.metadata.sorted_tables`, so adding a model table has operational effects (`app/routers/admin.py:73-86`, `alembic/env.py`).

Notable boundary leak: poller writes runtime dashboard state by importing `app.routers.dashboard` globals. That is an implementation constraint, not a separate service boundary.

## Databases, Schemas, and Migration Mechanisms

Database access:

- `DATABASE_URL` is required at import/startup; the backend raises immediately if it is absent (`app/database.py:7-12`).
- SQLAlchemy creates an engine with `pool_pre_ping=True` and a sessionmaker exposed as `SessionLocal`; request handlers use one DB session per request via `get_db()` (`app/database.py:14-24`).
- Production runtime is PostgreSQL via Compose (`docker-compose.yml`), while tests use in-memory SQLite with `StaticPool` (`conftest.py`).

Current ORM tables in `app/models.py`:

- `app_settings`: key/value settings, secret flag, `updated_at`.
- `cats`: name, active flag, reference weight, photo path, birth date, created timestamp.
- `cat_events` plus `cat_event_cats`: lifecycle events and shared event links.
- `visits`: cat assignment, identification source, start/end, duration evidence, weight/confidence, last weight time.
- `visit_diagnostics`: per-visit diagnostic events with JSON payloads.
- `cleaning_cycles`: start/end.
- `device_snapshots`: raw Tuya DPS JSON snapshots.
- `settings_history`: changed Tuya setting DPs.

Migration mechanism:

- `alembic/env.py` imports `DATABASE_URL`, `engine`, and `Base.metadata`, then sets the Alembic SQLAlchemy URL from `DATABASE_URL`.
- Migrations live under `alembic/versions/`, beginning with `0a98c1f83a12_initial_schema.py` and ending, by filename order inspected, with `a2b3c4d5e6f7_app_settings.py`.
- The Docker image command runs `alembic upgrade head` before starting Uvicorn (`Dockerfile`).
- Admin backup includes every SQLAlchemy-managed table except secret `app_settings` rows, plus uploads under `uploads/` (`app/routers/admin.py:73-86`, `app/routers/admin.py:285-304`).
- Restore validates archive structure, exact table set, row columns, and path safety before replacing DB rows and uploads (`app/routers/admin.py:97-213`, `app/routers/admin.py:307-330`).

## APIs, Events, Queues, and External Integrations

HTTP APIs verified from routers:

- `GET /health`
- `/dashboard`: `GET /dashboard`
- `/cats`: create/list/get/update, photo upload/delete, lifecycle event CRUD.
- `/visits`: create/list/summary/weight-history/get/update/delete, visit diagnostics.
- `/cleaning-cycles`: list recent cycles.
- `/display/summary`: ESP32-oriented status payload.
- `/diagnostics/summary`: diagnostic aggregate payload.
- `/admin/tuya-config`, `/admin/tuya-config/test`, `/admin/tuya-config/reload`: Tuya config management.
- `/admin/backup`, `/admin/restore/validate`, `/admin/restore`: backup/restore.
- `/webhook/tuya`: only included in webhook mode.
- FastAPI also exposes `/docs`, `/redoc`, and `/openapi.json`.

Events and queues:

- There is no external message queue in the repository.
- Internal event-like records are persisted as `VisitDiagnostic`, `SettingsHistory`, `DeviceSnapshot`, and `CleaningCycle`.
- Runtime poller state is in memory, with DB recovery of open visit/cleaning-cycle IDs at poller creation (`app/poller.py:135-168`).

External integrations:

- Tuya Cloud through `tinytuya.Cloud.getstatus()` and `cloudrequest("/v2.0/cloud/thing/{device_id}/report-logs", ...)` (`app/poller.py:59-68`, `app/poller.py:590+`).
- Optional Tuya webhook message subscription to `/webhook/tuya` (`app/routers/webhook.py:18-44`).
- Browser/React SPA served by FastAPI in deployed builds.
- ESP32 e-paper display consumes the display API over HTTP.
- Deployment script uses git, SSH, and Docker Compose against a NAS host (`deploy.sh`).

## Authentication and Authorization

There is no general authentication or authorization layer in the FastAPI app:

- No route dependency enforces a user/session/API-key check.
- `CORSMiddleware` allows all origins, methods, and headers (`app/main.py:90-95`).
- Admin routes for Tuya config, backup, and restore are mounted without auth dependencies (`app/routers/admin.py:255-330`).
- The only verified request secret is optional `WEBHOOK_SECRET` on `/webhook/tuya`, checked against `X-Webhook-Secret` when configured (`app/routers/webhook.py:15-22`).

This appears consistent with archived display spec language that v1 is LAN/local-app oriented, but it is a major operational assumption for any internet-exposed deployment.

## Configuration and Secrets Handling

Configuration sources:

- Required: `DATABASE_URL`.
- App mode: `UPDATE_MODE=polling|webhook`.
- Tuya fallback env: `TUYA_DEVICE_ID`, `TUYA_DEVICE_IP`, `TUYA_API_KEY`, `TUYA_API_SECRET`, `TUYA_API_REGION`.
- Tuya runtime config can be stored in DB `app_settings`; DB values override environment values once present (`app/settings.py:77-94`).
- Upload sizing/paths: `UPLOADS_DIR`, `MAX_CAT_PHOTO_BYTES`, `MAX_RESTORE_ARCHIVE_BYTES`.
- Polling behavior: `SNAPSHOT_INTERVAL_SECONDS`, adaptive polling variables, `VISIT_HARD_TIMEOUT_SECONDS`, `WEIGHT_OUTLIER_DELTA_KG`.
- Timezone: `APP_TIMEZONE`, default `Europe/Amsterdam` (`app/timezones.py`).
- Frontend API base URL: `VITE_API_URL`.
- Webhook shared secret: `WEBHOOK_SECRET`.

Secrets handling:

- Tuya API key/secret settings are flagged as secret in `app_settings` (`app/settings.py:22`, `app/settings.py:132-137`).
- Admin config status returns booleans for API key/secret presence, not secret values (`app/settings.py:97-106`).
- Backup excludes rows from `app_settings` where `is_secret` is true (`app/routers/admin.py:73-86`).
- Diagnostics recursively redacts payload keys containing secret/token/password/credential/api key/auth fragments (`app/routers/diagnostics.py`).
- `.env.example` instructs generated PostgreSQL passwords and empty Tuya values, but contains a malformed-looking `:   WEBHOOK_SECRET=` line instead of `WEBHOOK_SECRET=`.

## Build, Test, and Deployment Processes

Backend development and tests:

- Install with `pip install -r requirements.txt`.
- Run tests with `python3 -m pytest tests/ -v` or `.venv/bin/python -m pytest tests/ -v` per `docs/AGENTS.md`.
- Tests set default env vars before importing app modules and override `get_db()` with an in-memory SQLite session (`conftest.py`).
- Tuya access is mocked in tests; normal suite should not need live credentials.

Frontend:

- Install with `cd frontend && npm ci` or `npm install`.
- `npm run dev` starts Vite.
- `npm run lint`, `npm test`, and `npm run build` are the main verification commands.
- Vite build splits vendor chunks for React/router, Recharts, Axios/date-fns (`frontend/vite.config.js`).

Docker/deploy:

- `Dockerfile` builds the frontend in a Node stage, then copies backend, Alembic, and built frontend into a Python image; container command migrates then starts `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- `docker-compose.yml` runs app plus PostgreSQL 16, maps host `8001` to container `8000`, persists `postgres_data` and `uploads_data`, and passes database/Tuya/timezone env.
- `deploy.sh validate` creates/uses `.venv`, installs backend deps, runs backend tests, installs frontend deps with a local npm global config, runs lint/tests/build.
- `deploy.sh deploy` does `git pull --ff-only`, refuses dirty worktrees unless `ALLOW_DIRTY_DEPLOY=true`, validates, pushes, then SSHes to the NAS and runs `sudo docker compose up --build -d`.

Verification not performed for this research task: tests/build commands were not run because the task requested repository analysis and documentation only, not behavior changes.

## Existing Coding, Naming, and Testing Conventions

Backend conventions:

- Python modules use snake_case functions/variables and PascalCase ORM/Pydantic classes.
- Routers are grouped by resource under `app/routers/` with `APIRouter(prefix=..., tags=[...])`.
- SQLAlchemy models are declared centrally in `app/models.py`; Pydantic schemas in `app/schemas.py`.
- Datetimes are intended to be timezone-aware UTC through `TZDateTime`, `datetime.now(timezone.utc)`, and timezone helpers.
- Domain validation is mainly in Pydantic schemas and route-level explicit checks.

Frontend conventions:

- React function components, ES modules, `.jsx` views/components.
- Page components live under `frontend/src/pages`; reusable components under `frontend/src/components`.
- API calls are centralized in `frontend/src/api/client.js`.
- UI text is centralized in `frontend/src/i18n/translations.js` for English and Dutch.
- Theme preference and language are browser-local settings.
- ESLint treats unused variables as errors except uppercase ignore pattern (`frontend/eslint.config.js`).

Testing conventions:

- Backend tests use names like `test_api_cats.py`, `test_poller.py`, and function names starting `test_`.
- Test fixtures in `conftest.py` provide DB/session/client/poller isolation.
- Frontend tests use `*.test.jsx` beside source files and Vitest/Testing Library.
- Existing tests cover API CRUD, dashboard/display summaries, poller lifecycle/reconciliation/adaptive polling, device faults, health signals, OpenAPI, admin backup/restore/Tuya config, frontend pages/components, and UI primitives.

## Technically Important Legacy Constraints

- Polling interval is 300 seconds by default, chosen for Tuya API quota conservatism; adaptive polling exists but is bounded by interval, max window, daily budget, and cooldown (`app/main.py:20`, `app/poller.py:19-24`).
- Tuya status polling can miss short completion events; report-log reconciliation and hard-timeout behavior exist because duration evidence can be unreliable (`app/poller.py:469-560`).
- Legacy unknown 1800-second timeout durations are hidden from responses/aggregates by `trusted_duration` helpers and schema post-processing (`app/durations.py`, `app/schemas.py`).
- Cat identification by weight only auto-assigns when exactly one candidate is plausible within 0.5 kg; a recent-baseline fallback requires at least two prior identified weights (`app/cat_identifier.py`, `app/poller.py:862-904`).
- Reference weight is only nudged on successful non-suspect auto-identification at closure; early identification does not update reference weight (`app/poller.py:959-983`).
- The poller is stateful and in-memory, but recovers open visits and cleaning cycles from DB on startup (`app/poller.py:135-168`).
- App health in webhook mode is treated as healthy as long as the app is running; dashboard/display do not detect absence of incoming webhooks as stale (`app/routers/dashboard.py`, `app/routers/display.py`).
- Backup format is versioned as `BACKUP_FORMAT_VERSION = 1` and expects exact table names/columns on restore (`app/routers/admin.py`).
- Admin backup excludes secret settings, so Tuya API keys/secrets must be supplied again via environment or Admin after restore.
- Frontend browser navigation to `/cats`, `/cats/{id}`, and `/visits` has special backend handling to serve the SPA when the Accept header asks for HTML (`app/routers/cats.py`, `app/routers/visits.py`).

## Documentation and Implementation Disagreements

- `docs/SPECIFICATION.md` says `PATCH /visits/{visit_id}` updates visit metadata and manual `cat_id` changes set `identified_by` to `manual`, but the implementation also supports editing `started_at`, `duration_seconds`, `weight_kg`, and `weight_confidence` (`app/routers/visits.py:351-410`). README is more current on this point.
- `docs/SPECIFICATION.md` model summary for `Visit` omits `weight_confidence` and `weight_confidence_reason`, which exist in `app/models.py:110-112`, `app/schemas.py`, migrations, and tests.
- `docs/SPECIFICATION.md` says the frontend sidebar navigation is Dashboard, Visits, and Cats, but `frontend/src/App.jsx` also includes Admin, and Diagnostics is routed and linked from Admin/Dashboard.
- `.env.example` documents optional webhook secret with `:   WEBHOOK_SECRET=`. The implementation expects `WEBHOOK_SECRET` exactly (`app/routers/webhook.py:15`), and `docs/update-modes.md` documents the correct form.
- `README.md` says suspicious records should be corrected or marked ignored "once those workflows are implemented"; the implementation now includes `weight_confidence` editing and ignored weights are excluded from charts/summaries by default (`app/routers/visits.py`, tests in `tests/test_api_visits.py`).
- `docs/SPECIFICATION.md` says "No active polling thread is started" in webhook mode and "Tuya API credentials are not required at runtime"; the implementation does create a `LitterboxPoller` in webhook mode without cloud init, so API credentials are not needed for webhook processing, but Admin test/reload endpoints still exercise Tuya Cloud if used.

## Assumptions That Could Not Be Verified

- Live Tuya DP names, units, and report-log payload shapes were inferred from code/tests/docs; no live device or Tuya account was queried.
- The NAS deployment target, SSH access, Docker availability, and runtime environment variables were not verified.
- PostgreSQL migrations were inspected but not applied against a live database in this research pass.
- Frontend build, lint, tests, backend tests, and Docker image build were not executed for this documentation-only task.
- Whether deployment is intended to be LAN-only, VPN-only, or internet-exposed could not be fully verified from code. The code currently has no general app authentication.
- Current untracked `.agents`, `.github`, and `.specify` directories were not treated as shipped application source; their intended lifecycle is unverified.
- Actual ESP32 display rendering on hardware was not verified.
