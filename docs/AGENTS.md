# Repository Guidelines

## Project Structure & Module Organization

This repository contains a FastAPI backend and a Vite/React frontend for a Tuya-connected litterbox dashboard. Backend code lives in `app/`: routers in `app/routers/`, models in `app/models.py`, schemas in `app/schemas.py`, and polling logic in `app/poller.py` and `app/cat_identifier.py`. Backend tests are in `tests/`; shared pytest setup is in `conftest.py`. Alembic migrations live in `alembic/versions/`. Frontend source is in `frontend/src/`, with pages in `pages/`, components in `components/`, and assets in `public/` or `src/assets/`. Runtime uploads belong in `uploads/`.

## Build, Test, and Development Commands

- `pip install -r requirements.txt`: install backend dependencies.
- `python3 -m pytest tests/ -v`: run backend tests with mocked Tuya access and in-memory SQLite.
- `uvicorn app.main:app --reload --port 8000`: run the API locally.
- `alembic upgrade head`: apply database migrations.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start Vite.
- `cd frontend && npm run build`: build `frontend/dist/`.
- `cd frontend && npm run lint && npm test`: run ESLint and Vitest.
- If `node`/`npm` are not on PATH for the agent shell, use the local nvm install explicitly: `cd frontend && PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run lint` and `cd frontend && PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm test -- --run`.
- `docker compose up --build -d`: run the app and Postgres.

## Coding Style & Naming Conventions

Use Python 3 style with 4-space indentation, snake_case functions and variables, and PascalCase ORM/Pydantic classes. Keep FastAPI endpoints grouped by resource in `app/routers/`. Prefer timezone-aware datetimes, Pydantic schemas, and SQLAlchemy models. Frontend code uses ES modules, React function components, PascalCase component filenames, and `.jsx` for React views. Follow `frontend/eslint.config.js`; unused variables are errors unless they match the uppercase ignore pattern.

## Testing Guidelines

Add or update pytest tests in `tests/` for backend behavior, using names like `test_api_cats.py` and `test_poller.py`. Device and Tuya calls should stay mocked unless an integration test is explicit. Frontend tests live beside UI code as `*.test.jsx` and use Vitest with Testing Library. Run backend and frontend tests before submitting behavior changes.

## Agent Collaboration Guidelines

If an agent needs missing tools, credentials, dependency installs, command approval, audit output, deployment context, or any other user-provided input to proceed reliably, it should ask for that explicitly instead of silently skipping the step or guessing.

## Commit & Pull Request Guidelines

Git history uses short subjects such as `Fixed photo uploads`, `deploy: update`, and `Add support for webhooks`. Keep commits focused and avoid staging generated files, secrets, `.env`, snapshots, or local uploads. Pull requests should summarize the change, mention migrations or configuration updates, link issues when available, include screenshots for frontend changes, and list tests run.

## Security & Configuration Tips

Copy `tinytuya.json.example` or use environment variables for Tuya credentials; never commit real credentials. Docker Compose expects `POSTGRES_PASSWORD` and Tuya settings. `deploy.sh` uses `git add -u` to avoid staging untracked secrets.
