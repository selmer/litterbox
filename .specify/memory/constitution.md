<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Placeholder Principle 1 -> I. Evidence-Based Change Control
- Placeholder Principle 2 -> II. Runtime and Module Boundaries
- Placeholder Principle 3 -> III. Stable APIs and Data Contracts
- Placeholder Principle 4 -> IV. Database Durability and Migration Discipline
- Placeholder Principle 5 -> V. Security, Secrets, Observability, and Verification
Added sections:
- Supported Runtime and Framework Baseline
- Development Workflow and Quality Gates
- Legacy Code Rules
- Aspirational Improvements
Removed sections:
- Template placeholder sections only
Templates requiring updates:
- updated .specify/templates/plan-template.md
- updated .specify/templates/spec-template.md
- updated .specify/templates/tasks-template.md
Command files reviewed:
- reviewed .github/agents/speckit.*.agent.md and .agents/skills/speckit-*/SKILL.md
- updated .github/agents/speckit.tasks.agent.md
- updated .github/agents/speckit.implement.agent.md
- updated .agents/skills/speckit-tasks/SKILL.md
- updated .agents/skills/speckit-implement/SKILL.md
Runtime guidance reviewed:
- reviewed README.md
- reviewed docs/AGENTS.md
- reviewed docs/codebase-research.md
Follow-up TODOs:
- None
-->
# Litterbox Constitution

## Core Principles

### I. Evidence-Based Change Control

Mandatory existing constraints:

- Source code, tests, build configuration, migrations, Docker/deploy configuration, and
  `docs/codebase-research.md` are stronger evidence than prose documentation when they
  disagree.
- Non-trivial implementation work MUST be tracked through the active Spec Kit workflow
  under `docs/specs/`, with completed specs archived and indexed as described in
  `docs/AGENTS.md`.
- Repository automation MUST read `docs/AGENTS.md` before repository work.

Standards for new or changed code:

- Every feature spec and implementation plan MUST identify the existing files, APIs,
  schemas, tests, and deployment paths it relies on.
- If documentation and implementation disagree, the change MUST either update the
  documentation or explicitly record the disagreement as out of scope.
- New behavior MUST be covered by automated tests at the same boundary where the
  behavior is exposed: backend route/domain tests for API behavior, poller tests for
  Tuya ingestion behavior, frontend tests for UI workflows, and migration tests or
  smoke checks for schema-affecting changes.

Rationale: this is a small operational system connected to household hardware and
historical health data; changing it safely requires preserving what actually runs.

### II. Runtime and Module Boundaries

Mandatory existing constraints:

- The supported production runtime is the Docker stack defined by `Dockerfile` and
  `docker-compose.yml`: Python 3.13 slim, Node 22 slim for frontend build, PostgreSQL
  16 alpine, FastAPI 0.135, SQLAlchemy 2.0, Alembic 1.18, Pydantic 2.12, Uvicorn
  0.41, React 19, React Router 7, Vite 8, and Vitest 4.
- The supported local toolchain MAY use the repository virtualenv and the local nvm
  Node 24.15.0 path documented in `docs/AGENTS.md` for verification.
- Backend code lives in `app/`; routers live in `app/routers/`; ORM models live in
  `app/models.py`; Pydantic schemas live in `app/schemas.py`; poller/device logic
  lives in `app/poller.py`, `app/poller_runtime.py`, and `app/cat_identifier.py`.
- Frontend code lives in `frontend/src/`; pages, components, API client, and i18n
  modules stay in their existing directories.
- Alembic migrations live in `alembic/versions/`; firmware lives under
  `firmware/epaper-display/`; runtime uploads belong in `uploads/`.

Standards for new or changed code:

- Routers MUST depend inward on `app.database.get_db`, schemas, models, and domain
  helpers. Frontend modules MUST consume backend behavior only through HTTP APIs in
  `frontend/src/api/client.js`.
- Backend modules MUST NOT import frontend modules. Firmware MUST depend only on the
  documented `/display/summary` JSON contract and local firmware configuration.
- New shared helpers MUST be placed in `app/` only when used by multiple routers or by
  poller plus routers; otherwise keep logic near the owning router/domain.
- Changes MUST preserve timezone-aware datetime handling and the existing local-day
  boundary behavior unless a spec explicitly changes those semantics.

Rationale: the existing architecture is intentionally simple. Module ownership keeps
API, poller, persistence, UI, and firmware changes independently testable.

### III. Stable APIs and Data Contracts

Mandatory existing constraints:

- Public HTTP contracts include FastAPI routes, OpenAPI output, frontend calls in
  `frontend/src/api/client.js`, webhook payload handling, backup archive format v1,
  and the ESP32 `/display/summary` contract.
- `/webhook/tuya` exists only in webhook mode. Polling mode starts the background
  poller; webhook mode creates a webhook poller without active polling.
- Existing visit duration semantics distinguish trusted durations from untrusted or
  legacy fallback durations. Untrusted durations are hidden from user-facing duration
  totals and response fields where current schemas do so.
- Existing backup archives exclude secret `app_settings` rows and include database
  JSON plus uploads.

Standards for new or changed code:

- API changes MUST be backwards-compatible for existing frontend and firmware clients
  unless the spec declares a breaking change and updates all in-repo clients, tests,
  and documentation in the same change.
- Response fields may be added when clients can ignore them. Existing field names,
  meanings, units, enum values, status codes, and archive layout MUST NOT be changed
  silently.
- Webhook, Tuya DP, display, backup/restore, and OpenAPI changes MUST include tests
  that exercise the contract boundary.
- Frontend navigation fallback behavior for browser routes served by FastAPI MUST be
  preserved for existing routes unless an explicit routing migration is documented.

Rationale: the frontend, firmware, backup files, and Tuya webhook configuration are
separate clients of the backend. Contract drift creates operational failures.

### IV. Database Durability and Migration Discipline

Mandatory existing constraints:

- `DATABASE_URL` is required before app/database imports can succeed.
- Production storage is PostgreSQL through Docker Compose; tests use SQLite where the
  current suite does so.
- SQLAlchemy ORM models in `app/models.py` are the authoritative application schema,
  and Alembic migrations are the mechanism for changing persisted structure.
- Docker startup runs `alembic upgrade head` before Uvicorn.
- Admin backup/restore iterates `Base.metadata.sorted_tables`, so model table changes
  affect backup compatibility.

Standards for new or changed code:

- Any schema change MUST include an Alembic migration under `alembic/versions/`.
- Migrations MUST preserve existing household history or document an intentional,
  reviewed data transformation. Destructive migrations require explicit spec coverage,
  rollback/backup guidance, and tests or a migration smoke check.
- Model, schema, router, backup/restore, and tests MUST be updated together when data
  shape changes.
- New persisted timestamps MUST be timezone-aware UTC at the application boundary.
- New backup-relevant tables or columns MUST be validated against backup/restore tests.

Rationale: the database is the long-lived record of visits, weights, photos, lifecycle
events, diagnostics, and configuration. Data loss is more serious than code churn.

### V. Security, Secrets, Observability, and Verification

Mandatory existing constraints:

- There is no general application authentication layer today. This MUST be treated as
  an existing deployment constraint, not as evidence that internet exposure is safe.
- `WEBHOOK_SECRET` is the only implemented request secret, and it applies only to the
  webhook route when configured.
- Tuya API key and secret values may be stored as secret `app_settings` rows and MUST
  be masked in status responses and excluded from backups.
- Runtime uploads, generated files, local device data, credentials, `.env`, and real
  Tuya artifacts MUST NOT be committed.
- Diagnostics redact sensitive-looking payload keys before returning recent diagnostic
  payloads.

Standards for new or changed code:

- New admin, restore, credential, upload, diagnostics, webhook, or external-integration
  behavior MUST identify its threat model in the spec and MUST avoid logging or
  returning secrets.
- New file upload or archive handling MUST validate size, content/type expectations,
  and path traversal risks.
- New operationally significant failures MUST be observable through structured logs,
  diagnostics, health state, persisted diagnostic rows, or explicit UI error states.
- Required automated tests for changed behavior MUST pass before merge. Mock Tuya
  access by default; live hardware/cloud tests are optional and MUST be isolated from
  the normal suite.

Rationale: this project handles local network details, Tuya credentials, household
activity, photos, backups, and operational diagnostics. Safety depends on both secrecy
and debuggability.

## Supported Runtime and Framework Baseline

Mandatory existing constraints:

- Backend production container: Python 3.13 slim.
- Frontend build container: Node 22 slim.
- Database: PostgreSQL 16 alpine in Compose.
- Backend frameworks and libraries: FastAPI 0.135, Starlette 0.52, SQLAlchemy 2.0,
  Alembic 1.18, Pydantic 2.12, Uvicorn 0.41, tinytuya 1.17.
- Frontend frameworks and libraries: React 19, React DOM 19, React Router 7, Vite 8,
  Vitest 4, Recharts 3, Axios 1.
- Firmware framework: PlatformIO Arduino ESP32 with ArduinoJson, GxEPD2, and Adafruit
  GFX as declared in `firmware/epaper-display/platformio.ini`.

Standards for new or changed code:

- Dependency upgrades MUST update lockfiles/manifests together, run the affected test
  and build commands, and document compatibility risks.
- Major dependency upgrades MUST be treated as behavior-affecting changes and require
  focused tests plus a rollback plan.
- New dependencies MUST be justified by removing meaningful complexity or matching an
  existing framework boundary.

Aspirational improvements:

- Establish an explicit dependency update cadence and changelog for runtime/library
  version bumps.
- Add automated dependency audit reporting to the merge process.

## Development Workflow and Quality Gates

Mandatory existing constraints:

- `docs/AGENTS.md` is authoritative for repository automation and verification
  fallbacks.
- Backend tests use pytest with mocked Tuya access and in-memory SQLite.
- Frontend tests use Vitest and Testing Library.
- `deploy.sh validate` is the deployment validation path and runs backend tests,
  frontend install, lint, tests, and build.

Standards for new or changed code:

- Before merging backend behavior changes, run:
  - `.venv/bin/python -m pytest tests/ -v` when the local virtualenv is available, or
    `python3 -m pytest tests/ -v` when dependencies are available there.
- Before merging frontend behavior changes, run from `frontend/`:
  - `npm run lint`
  - `npm test`
  - `npm audit`
- Before merging frontend dependency/configuration changes, also run:
  - `npm run build`
- Before merging schema changes, run:
  - `alembic upgrade head` against a disposable or development database, or document
    why only a migration/code review was possible.
- Before deployment or release changes, run:
  - `./deploy.sh validate`
- If a required command cannot run because tools, dependencies, credentials, or command
  approval are unavailable, the final report MUST state the blocker and MUST NOT imply
  the gate passed.

Aspirational improvements:

- Add continuous integration that executes the same backend, frontend, audit, build,
  and migration checks on pull requests.
- Add a dedicated route/import smoke test for packaged Docker images.

## Legacy Code Rules

Mandatory existing constraints:

- The poller is stateful and in-memory but recovers open visits and cleaning cycles
  from the database.
- The poller currently publishes runtime health/fault state through dashboard router
  globals. This is an existing implementation constraint.
- Tuya status polling can miss short completion events; report-log reconciliation and
  hard-timeout behavior are required compatibility paths.
- Cat identification uses conservative weight matching and recent-baseline fallback;
  ambiguous matches remain unidentified.
- Webhook mode currently treats app process availability as poller health.

Standards for new or changed code:

- Legacy compatibility paths MUST remain covered by tests when touched.
- Refactors MUST preserve current behavior unless the spec explicitly authorizes a
  behavior change and updates tests/docs in the same change.
- Changes around visit duration, identification, weight confidence, backup/restore,
  upload paths, and Tuya DP handling MUST include regression tests for legacy and edge
  cases.
- Do not rewrite poller state management, routing, auth posture, or backup format as an
  incidental cleanup inside unrelated feature work.

Aspirational improvements:

- Replace router-global poller status with an explicit runtime state service.
- Add authenticated access control for admin and sensitive APIs before any non-LAN
  deployment is supported.
- Add stronger webhook authenticity checks if Tuya or deployment infrastructure
  supports them.
- Add end-to-end tests for Docker startup, migration, frontend serving, and display
  contract compatibility.

## Aspirational Improvements

These items are not claimed as implemented and MUST NOT be used to block unrelated
maintenance unless a spec adopts them:

- General application authentication and authorization for admin/sensitive routes.
- CI that runs backend tests, frontend lint/tests/build, npm audit, and migration smoke
  checks.
- Structured JSON logging and metrics collection.
- Explicit API versioning beyond current backwards-compatible route evolution.
- Automated OpenAPI contract comparison for breaking-change detection.
- Live Tuya/hardware integration tests gated behind explicit credentials and hardware
  availability.

## Governance

- This constitution supersedes conflicting generated specs, plans, and tasks. If it
  conflicts with `docs/AGENTS.md`, repository automation MUST pause and ask for a
  governance clarification rather than guessing.
- Amendments require a concrete repository need, evidence from current implementation
  or accepted project direction, updates to affected Spec Kit templates, and a Sync
  Impact Report in this file.
- Versioning policy:
  - MAJOR: removes or redefines a mandatory principle in a way that invalidates
    existing accepted specs or merge gates.
  - MINOR: adds a new principle, required gate, or materially expands scope.
  - PATCH: clarifies wording without changing compliance obligations.
- Every feature plan MUST include a Constitution Check and resolve violations before
  implementation tasks are generated.
- Reviews MUST verify the relevant mandatory constraints and standards for changed
  files. Aspirational improvements are tracked separately and are not evidence that
  current code already satisfies them.

**Version**: 1.0.0 | **Ratified**: 2026-07-13 | **Last Amended**: 2026-07-13
