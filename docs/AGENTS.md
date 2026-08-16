# Repository Guidelines

This is the authoritative project guidance for Codex and any future repository automation. The root `AGENTS.md` exists only as a bootstrap that points here before work begins.

## Project Structure & Module Organization

This repository contains a FastAPI backend and a Vite/React frontend for a Tuya-connected litterbox dashboard. Backend code lives in `app/`: routers in `app/routers/`, models in `app/models.py`, schemas in `app/schemas.py`, and polling logic in `app/poller.py` and `app/cat_identifier.py`. Backend tests are in `tests/`; shared pytest setup is in `conftest.py`. Alembic migrations live in `alembic/versions/`. Frontend source is in `frontend/src/`, with pages in `pages/`, components in `components/`, and assets in `public/` or `src/assets/`. Runtime uploads belong in `uploads/`.

## Build, Test, and Development Commands

- `pip install -r requirements.txt`: install backend dependencies.
- `python3 -m pytest tests/ -v`: run backend tests with mocked Tuya access and in-memory SQLite.
- In this workspace, prefer the local virtualenv when system Python lacks dependencies: `.venv/bin/python -m pytest tests/ -v`.
- FastAPI import or route smoke checks require `DATABASE_URL`; for a disposable local smoke check, use `DATABASE_URL=sqlite:////tmp/litterbox-route-smoke.db .venv/bin/python ...`.
- `uvicorn app.main:app --reload --port 8000`: run the API locally.
- `alembic upgrade head`: apply database migrations.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start Vite.
- `cd frontend && npm run build`: build `frontend/dist/`.
- `cd frontend && npm run lint && npm test`: run ESLint and Vitest.
- Before declaring `node`, `npm`, or `docker` unavailable, check this file for workspace-specific tool locations. If `node`/`npm` are not on PATH for the agent shell, rerun frontend commands with the local nvm install explicitly: `cd frontend && PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run lint` and `cd frontend && PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm test -- --run`.
- When running a single frontend test from inside `frontend/`, pass paths relative to that directory, for example `npm test -- --run src/pages/Visits.test.jsx`.
- For frontend code changes, verify with lint, relevant Vitest tests, and `npm audit`; do not infer audit status from test output. For dependency/configuration changes, also run `npm run build`. Use the nvm PATH override above whenever needed.
- Any warning, vulnerability, or error from a required npm, package-manager, or dependency-audit command must be resolved before coding is declared complete. This includes host-global configuration warnings such as `Unknown global config "tmp"`; if the repository cannot safely resolve one, report the work as blocked and ask the user to fix or authorize the external configuration change.
- For `npm audit` findings, inspect with `npm audit --json` and `npm ls <package>` to understand dependency paths. Do not suppress findings, run `npm audit fix --force`, or accept major breaking upgrades blindly; prefer targeted updates such as `npm update <transitive-package>` or focused direct dependency upgrades, then rerun `npm audit`, `npm run lint`, relevant tests, and `npm run build`. Ask the user if the safe fix is unclear.
- If a required verification command fails because dependencies or tools are missing, ask the user for help installing or exposing them before treating the verification as skipped.
- `docker compose up --build -d`: run the app and Postgres.

## Coding Style & Naming Conventions

Use Python 3 style with 4-space indentation, snake_case functions and variables, and PascalCase ORM/Pydantic classes. Keep FastAPI endpoints grouped by resource in `app/routers/`. Prefer timezone-aware datetimes, Pydantic schemas, and SQLAlchemy models. Frontend code uses ES modules, React function components, PascalCase component filenames, and `.jsx` for React views. Follow `frontend/eslint.config.js`; unused variables are errors unless they match the uppercase ignore pattern.

## Testing Guidelines

Add or update pytest tests in `tests/` for backend behavior, using names like `test_api_cats.py` and `test_poller.py`. Device and Tuya calls should stay mocked unless an integration test is explicit. Frontend tests live beside UI code as `*.test.jsx` and use Vitest with Testing Library. Run backend and frontend tests before submitting behavior changes.

## Planning & Spec Workflow

Use `docs/specs/` as the only active planning location for non-trivial implementation work. Completed specs move to `docs/specs/archive/` and their links in `docs/IMPROVEMENT_SPECIFICATIONS.md` should be updated in the same cleanup. Do not recreate ad-hoc planning folders such as `Plans/` or `MEMORY/`. Keep generated files, local device data, credentials, and runtime uploads out of git.

## Agent Collaboration Guidelines

If an agent needs missing tools, credentials, dependency installs, command approval, audit output, deployment context, or any other user-provided input to proceed reliably, it should ask for that explicitly instead of silently skipping the step or guessing.

## Commit & Pull Request Guidelines

Git history uses short subjects such as `Fixed photo uploads`, `deploy: update`, and `Add support for webhooks`. Keep commits focused and avoid staging generated files, secrets, `.env`, snapshots, or local uploads. Pull requests should summarize the change, mention migrations or configuration updates, link issues when available, include screenshots for frontend changes, and list tests run.

## Security & Configuration Tips

Copy `tinytuya.json.example` or use environment variables for Tuya credentials; never commit real credentials. Docker Compose expects `POSTGRES_PASSWORD` and Tuya settings. `deploy.sh` uses `git add -u` to avoid staging untracked secrets.
