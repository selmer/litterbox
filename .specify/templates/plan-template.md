# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for this repository. Use docs/codebase-research.md, docs/AGENTS.md, source code,
  tests, dependency manifests, migrations, and deployment configuration as evidence.
-->

**Language/Version**: [Python 3.13 backend container, Node 22 frontend build container, React 19, or NEEDS CLARIFICATION]

**Primary Dependencies**: [FastAPI, SQLAlchemy, Alembic, Pydantic, tinytuya, React, Vite, Vitest, etc.]

**Storage**: [PostgreSQL via SQLAlchemy/Alembic, uploads volume, app_settings, or N/A]

**Testing**: [pytest tests under tests/, Vitest/Testing Library under frontend/src, migration smoke checks when relevant]

**Target Platform**: [Docker Compose app+Postgres, browser SPA, optional ESP32 firmware, or NEEDS CLARIFICATION]

**Project Type**: [FastAPI + Vite/React web app with optional ESP32 firmware]

**API/Contract Impact**: [List affected routes, OpenAPI behavior, frontend client calls, webhook/display/backup contracts, or "None"]

**Database/Migration Impact**: [Model/table/column changes and Alembic migration requirement, or "None"]

**Security/Secrets Impact**: [Admin/credential/upload/webhook/diagnostics exposure and secret handling, or "None"]

**Observability Impact**: [Logs, diagnostics, health state, UI error state, or persisted diagnostics required]

**Legacy Constraints**: [Poller state, duration trust, Tuya DP behavior, backup format, SPA fallback, or "None"]

**Scale/Scope**: [Household self-hosted deployment assumptions and data volume impact, or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Evidence and scope: Plan cites current code/tests/config/docs used as evidence and notes any documentation drift.
- Runtime and boundaries: Uses existing FastAPI/SQLAlchemy/Alembic/Pydantic backend, Vite/React frontend, and module ownership unless a justified exception is recorded.
- API compatibility: Existing frontend, firmware, webhook, backup, OpenAPI, and display contracts are preserved or breaking changes are explicit and fully migrated.
- Database durability: Schema changes include Alembic migration, data preservation/rollback notes, and backup/restore impact.
- Security and secrets: Secret values are not logged, returned, committed, or included in backups; new sensitive surfaces describe the threat model.
- Observability: Operational failures are visible through logs, diagnostics, health state, persisted diagnostic rows, or UI error states.
- Tests and gates: Required backend/frontend/migration/deploy commands are identified for the touched areas.
- Legacy behavior: Duration trust, poller recovery, Tuya DP handling, identification, backup format, and SPA fallback regressions are covered when touched.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── routers/
├── models.py
├── schemas.py
├── database.py
├── poller.py
└── [domain helpers]

tests/
└── test_*.py

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── api/
│   └── i18n/
└── package.json

alembic/
└── versions/

firmware/epaper-display/
└── [PlatformIO firmware, if affected]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
