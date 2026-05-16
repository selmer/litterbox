# Litterbox Improvement Specifications

Generated from a repository assessment on 2026-05-16. This document is a specification pack only; it does not authorize implementation without an explicit follow-up request.

## Assessment Scope

Reviewed backend, frontend, tests, deployment scripts, migrations, and existing documentation. Key source areas inspected:

- Backend: `app/main.py`, `app/poller.py`, `app/models.py`, `app/schemas.py`, `app/routers/*`
- Frontend: `frontend/src/App.jsx`, `frontend/src/pages/*`, `frontend/src/components/*`, `frontend/src/api/client.js`
- Operations: `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `requirements.txt`, `frontend/package.json`
- Tests and docs: `tests/*`, `frontend/src/**/*.test.jsx`, `README.md`, `docs/*`

Verification could not be executed in this environment because `pytest`, `npm`, and `docker` are not installed, and the default command sandbox cannot start because `bubblewrap` is unavailable.

## Specification-First Working Rule

No application code change should be made unless a written specification exists first. For this repository, an implementation-ready specification should include:

- Problem statement and affected users/operators.
- Current behavior with file references.
- Proposed behavior.
- Data model, API, UI, and configuration impacts, if any.
- Acceptance criteria.
- Verification plan.
- Rollback or migration notes when runtime data can be affected.

## Prioritized Improvement Specifications

### Mini-spec: Pydantic v2 Config Deprecation Cleanup

Priority: P2

Problem:
Backend tests emit Pydantic v2 deprecation warnings because response schemas in `app/schemas.py` still use class-based `Config` for `from_attributes`.

Proposed behavior:

- Replace class-based `Config` with `model_config = ConfigDict(from_attributes=True)`.
- Keep API response shapes unchanged.
- Do not change validation rules or database behavior.

Acceptance criteria:

- `CatOut`, `VisitOut`, and `CleaningCycleOut` use Pydantic v2 `ConfigDict`.
- Backend tests pass without the three Pydantic `Config` deprecation warnings.

Verification:

- Run `python3 -m pytest tests/ -q`.

### Mini-spec: Frontend Lint Gate Cleanup

Priority: P1

Problem:
Frontend lint blocks deployment because toast code exports a hook from the same module as components, several tests use Vitest globals without importing them, and a few imports are unused.

Proposed behavior:

- Keep `Toast.jsx` component-only for React Fast Refresh.
- Move the toast context hook to a small shared module and update existing imports.
- Import Vitest globals explicitly in tests that use them.
- Remove unused imports.

Acceptance criteria:

- `npm run lint` passes for the affected frontend files.
- Toast runtime behavior and tests remain unchanged.

Verification:

- Run `npm run lint`.

### Mini-spec: Frontend Dependency Audit Cleanup

Priority: P1

Problem:
`npm audit` reports frontend dependency vulnerabilities in packages used directly or transitively by the Vite/React frontend, including `axios`, `vite`, `picomatch`, `postcss`, `follow-redirects`, and `brace-expansion`.

Proposed behavior:

- Run the non-force audit remediation path first: `npm audit fix`.
- Allow package lockfile updates and compatible dependency patch/minor updates.
- Do not use `npm audit fix --force` without a separate specification, because that may introduce breaking upgrades.
- Keep frontend runtime behavior unchanged.

Acceptance criteria:

- `npm audit` reports no remaining vulnerabilities, or any remaining issue is documented with the reason it cannot be safely fixed automatically.
- `npm run lint`, `npm test`, and `npm run build` pass after dependency remediation.

Verification:

- Run `npm audit`.
- Run `npm run lint`.
- Run `npm test`.
- Run `npm run build`.

### 1. Accurate Runtime Health and Poller Status

Priority: P0

Problem:
The polling loop updates `last_successful_poll_at` immediately after every `poller.poll()` call in `app/main.py:40-42`, even when `poll()` returns after cloud initialization failure, cloud read failure, unexpected responses, or empty DPs in `app/poller.py:93-114`.

Current behavior:

- Polling mode can look healthy while device reads are failing.
- `/health` only returns process liveness in `app/main.py:87-89`.

Proposed behavior:

- Track explicit poll outcomes: success, skipped, failed, last error, and last attempted timestamp.
- Update `last_successful_poll_at` only when cloud device state is processed successfully.
- Add health response fields or a separate status endpoint for device update health.

Acceptance criteria:

- Failed cloud responses do not refresh the dashboard's successful poll timestamp.
- Dashboard status distinguishes process health from device update health.
- Tests cover successful polling, failed polling, and stale polling cases.

Verification:

- Add backend tests for `LitterboxPoller.poll()` outcome reporting.
- Add dashboard tests for polling health states.
- Manually simulate failed Tuya responses and confirm dashboard health turns unhealthy.

### 2. Durable Poller State and Restart Recovery

Priority: P0

Problem:
Active visit and cleaning-cycle state is held in memory through `current_visit_id`, `current_cleaning_cycle_id`, and `last_weight_at` in `app/poller.py:62-67`. If the process restarts during a visit or cleaning cycle, the app can lose in-progress state and fail to close records correctly.

Current behavior:

- Visit start, weight updates, visit completion, timeout, and cleaning cycle state are tracked by a single process-local poller instance.
- There is no startup recovery for open `Visit` or `CleaningCycle` rows.
- `last_weight_at` is not persisted, so timeout behavior cannot survive restart.

Proposed behavior:

- Persist enough in-progress state to recover after restart.
- On startup, rehydrate open visits and open cleaning cycles from the database.
- Store last weight timestamp, latest raw weight, and device event counters when needed for deterministic recovery.
- Define duplicate and out-of-order DP handling for restart windows.

Acceptance criteria:

- A visit started before restart can be completed or timed out after restart.
- A cleaning cycle started before restart can be ended after restart.
- Startup recovery is deterministic when multiple open records exist.
- Recovery logs enough context for operators to understand what happened.

Verification:

- Add tests that create open records, instantiate a fresh poller, and process completion events.
- Add tests for timeout after restart.
- Run migration tests if a new state table or columns are added.

### 3. API Domain Validation and Referential Integrity

Priority: P1

Problem:
Pydantic schemas in `app/schemas.py:8-56` accept broad primitive types without domain constraints. Visit creation in `app/routers/visits.py:14-27` accepts any `cat_id`, duration, timestamp, and weight. Visit reassignment in `app/routers/visits.py:112-124` can set `identified_by` and does not validate target cat existence. Cat creation and update in `app/routers/cats.py:30-64` accept blank names and any reference weight value.

Current behavior:

- Negative or unrealistic weights can be accepted by API schemas.
- Manual visits can reference nonexistent cats.
- `identified_by` can be client-controlled on visit update.
- `offset` lacks an explicit non-negative query constraint in `app/routers/visits.py:30-43`.

Proposed behavior:

- Add schema constraints for names, weights, durations, limits, offsets, and timestamps.
- Validate `cat_id` on manual visit creation and reassignment.
- Treat `identified_by` as server-owned except for explicit, documented admin operations.
- Return consistent 400 or 422 errors with actionable messages.

Acceptance criteria:

- Blank cat names are rejected.
- Negative, zero, or unrealistic weights and durations are rejected according to documented bounds.
- Nonexistent `cat_id` values are rejected on visit creation and reassignment.
- Reassigning a visit to `null` deliberately marks it as visitor/unidentified using documented semantics.

Verification:

- Add backend API tests for invalid cats, invalid visits, invalid pagination, and reassignment edge cases.
- Confirm frontend validation messages match backend constraints.

### 4. Safe and Durable Cat Photo Storage

Priority: P1

Problem:
Photo upload accepts any `data:image/*` prefix, decodes unbounded base64, writes the bytes as `{cat_id}.jpg`, and stores a relative file path in `app/routers/cats.py:67-93`. Deletion trusts the stored path in `app/routers/cats.py:102-105`. Docker Compose persists only Postgres data, not uploads.

Current behavior:

- Server-side file type and image validity are not verified.
- Upload size is not constrained.
- Runtime uploads may be lost when containers are rebuilt.
- Stored path handling is more permissive than needed.

Proposed behavior:

- Enforce maximum encoded and decoded upload sizes.
- Verify actual image content server-side and normalize to a safe format.
- Store only controlled relative filenames or object keys, never arbitrary paths.
- Add a persistent uploads volume or move photos to external object storage.
- Serve uploaded files with safe content headers.

Acceptance criteria:

- Non-image payloads with an image data URL prefix are rejected.
- Oversized payloads are rejected before excessive memory use.
- Uploaded photos survive container rebuilds.
- Deleting a photo cannot remove files outside the configured photo directory.

Verification:

- Add API tests for valid upload, invalid base64, wrong MIME, oversized image, and delete safety.
- Add Compose verification that `uploads` is mounted persistently.

### 5. Deterministic and Scalable Dashboard Queries

Priority: P1

Problem:
Dashboard aggregation performs useful SQL work, but the latest-visit join in `app/routers/dashboard.py:46-81` can duplicate cat rows when two visits share the same max `started_at`. Weight history performs one query per cat in `app/routers/visits.py:70-81`, which will scale poorly as cats and history grow.

Current behavior:

- Latest visit selection is not deterministic on timestamp ties.
- Weight history uses an N+1 query pattern.
- Cleaning-cycle date filters rely on current indexes and may need explicit support as data grows.

Proposed behavior:

- Use deterministic latest-visit selection with tie-breaking by visit ID or a window function.
- Fetch weight history for all cats in one query and group in application code.
- Add or confirm indexes for common filters: `visits(cat_id, started_at)`, `visits(started_at)`, and cleaning-cycle start time.
- Document expected dashboard query performance with a realistic record count.

Acceptance criteria:

- Dashboard returns one row per active cat under timestamp ties.
- Weight history uses a bounded number of queries independent of cat count.
- Query plans use indexes for common dashboard and chart requests.
- API behavior remains unchanged except for deterministic tie handling.

Verification:

- Add tests for same-timestamp latest visits.
- Add tests or instrumentation proving weight history does not issue one query per cat.
- Run explain plans against PostgreSQL with representative data.

### 6. Time-Series Weight Chart Correctness

Priority: P1

Problem:
The weight chart groups points by `format(timestamp, 'dd MMM')` in `frontend/src/components/WeightChart.jsx:43-58`, which loses the year, overwrites multiple same-day points for a cat, and sorts with `new Date(a.date)` on incomplete date strings.

Current behavior:

- Multi-year ranges can merge different years into the same date key.
- Multiple visits on the same day overwrite earlier values for the same cat.
- Sorting depends on JavaScript parsing of partial localized date strings.

Proposed behavior:

- Use stable timestamp keys, such as ISO date or full timestamp depending on desired granularity.
- Preserve multiple points per day or explicitly aggregate by day with a documented rule.
- Sort by numeric timestamp.
- Format labels only at render time.

Acceptance criteria:

- A one-year and all-time chart preserves year boundaries.
- Multiple same-day visits do not silently disappear unless an aggregation rule says so.
- Chart ordering is stable across browsers and locales.
- Tooltip labels display human-readable dates while data keys remain machine-stable.

Verification:

- Add frontend tests for cross-year data, same-day multiple visits, and ordering.
- Manually inspect chart behavior with synthetic multi-year data.

### 7. Frontend Data Fetching, Error States, and Freshness

Priority: P1

Problem:
Dashboard initial loading fetches dashboard, weight history, recent visits, and cats in `frontend/src/pages/Dashboard.jsx:55-73`, but the 15-second refresh updates only the dashboard summary in `frontend/src/pages/Dashboard.jsx:79-83`. The Visits page suppresses dependency linting for its fetch effect in `frontend/src/pages/Visits.jsx:23-46` and does not expose retry or persistent error UI.

Current behavior:

- Dashboard cards refresh but recent visits, cats, and charts can become stale.
- API failures often collapse to generic messages or console logs.
- Some fetch paths lack cancellation or stale-response protection.

Proposed behavior:

- Centralize API error handling and normalize user-visible error messages.
- Refresh dashboard-adjacent data according to clear freshness rules.
- Add request cancellation or stale-response guards for page/filter changes.
- Replace the Visits fetch dependency suppression with stable callbacks or a small data-fetch helper.

Acceptance criteria:

- Recent visits update after an automatic device visit without full page reload.
- Failed API requests show actionable retry affordances.
- Rapid filter changes on Visits cannot display stale results from older requests.
- Lint can run without disabling hook dependency checks for data fetching.

Verification:

- Add frontend tests for dashboard refresh, Visits filter race handling, and error retry states.
- Run `npm run lint` and `npm test`.

### 8. Deployment and Release Pipeline Hardening

Priority: P1

Problem:
`deploy.sh` pulls, installs dependencies, runs backend tests, builds frontend, commits local tracked changes, pushes, and SSH deploys in one script (`deploy.sh:10-49`). It does not run frontend tests or lint, uses hard-coded NAS details, runs `npm install` rather than `npm ci`, and changes `node_modules` ownership with sudo.

Current behavior:

- Deployment mutates local git state and may commit unrelated tracked changes.
- Frontend quality gates are omitted from deploy.
- Environment assumptions are embedded in the script.
- Local missing tools break verification, as seen in this assessment environment.

Proposed behavior:

- Split validation, packaging, and deployment into separate commands.
- Use reproducible installs: `pip` in a virtual environment or container, and `npm ci`.
- Add frontend lint/test/build gates.
- Move NAS host/path/user to environment variables or a deploy config excluded from git.
- Prefer CI or a containerized validation command that matches production.

Acceptance criteria:

- A validation command can run without committing or deploying.
- Deployment refuses to proceed with dirty unrelated changes unless explicitly allowed.
- Frontend lint and tests are required before deployment.
- NAS details are configurable without editing the script.

Verification:

- Add a dry-run validation mode.
- Run backend tests, frontend lint, frontend tests, and frontend build in the release workflow.
- Confirm deploy works from a clean checkout.

### 9. Documentation and Test Coverage Trustworthiness

Priority: P2

Problem:
Documentation and test inventories need to stay synchronized with the repository so contributors can trust the verification instructions.

Current behavior:

- Test documentation can drift from the actual test inventory without an explicit checklist.
- Some important behaviors lack tests: photo upload hardening, visit API edge cases, deployment workflow, and frontend chart correctness.
- New contributors may run the wrong verification set.
- Push/webhook/pub-sub work is intentionally deferred to a future dedicated specification.

Proposed behavior:

- Maintain a generated or manually verified test inventory in docs.
- Add missing tests for visit API, photo upload, chart behavior, and health semantics.
- Add a lightweight docs verification checklist to future specs.
- Update `docs/SPECIFICATION.md` whenever public behavior changes.

Acceptance criteria:

- README and specification list only tests that exist.
- Each implemented improvement includes matching test additions or an explicit no-test rationale.
- New specs include documentation-update requirements.
- The repository has one authoritative verification command list.

Verification:

- Run `rg --files tests frontend/src | rg 'test'` and compare with docs.
- Run backend and frontend test suites in an environment with required tools.
- Review docs in the same PR as behavior changes.
