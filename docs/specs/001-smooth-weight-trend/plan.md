# Implementation Plan: Smooth Weight Trend

**Branch**: `001-smooth-weight-trend` | **Date**: 2026-07-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `docs/specs/001-smooth-weight-trend/spec.md`

## Summary

Make the dashboard weight trend graph easier to read by deriving a presentation-only smoothed series for each cat from the existing `/visits/weight-history` measurements. The original measurement values remain the source of truth and stay available in chart tooltip context. No backend storage, migration, firmware, backup, Tuya, or display API changes are planned.

## Technical Context

**Language/Version**: Frontend JavaScript ES modules with React 19, Vite 8, Vitest 4; backend remains Python 3.13/FastAPI 0.135 without planned changes.

**Primary Dependencies**: Existing Recharts 3 charting in `frontend/src/components/WeightChart.jsx`, date-fns formatting, React Testing Library/Vitest tests. Existing Axios client in `frontend/src/api/client.js` continues to call FastAPI.

**Storage**: PostgreSQL-backed `visits.weight_kg` remains unchanged. No new persisted storage, uploads, app settings, or derived trend cache.

**Testing**: Frontend Vitest/Testing Library coverage in `frontend/src/components/WeightChart.test.jsx`; existing backend `/visits/weight-history` behavior remains covered by backend route tests if untouched. Run frontend lint, relevant Vitest test, and npm audit for the frontend behavior change.

**Target Platform**: Browser SPA served by the existing FastAPI/Docker Compose deployment.

**Project Type**: FastAPI + Vite/React web app with optional ESP32 firmware. This feature is scoped to the React dashboard chart.

**API/Contract Impact**: Existing `GET /visits/weight-history` response shape is consumed unchanged: `cat_id`, `cat_name`, and data points with `timestamp`, `weight_kg`, `visit_id`, `weight_confidence`. No OpenAPI or firmware contract change planned.

**Database/Migration Impact**: None. No model, table, column, Alembic migration, backup, or restore format changes.

**Security/Secrets Impact**: None. The feature presents existing household weight data and does not touch credentials, admin, uploads, diagnostics payloads, or webhooks.

**Observability Impact**: User-facing chart state only. Sparse-data behavior remains visible through the graph displaying raw points or the existing no-data empty state.

**Legacy Constraints**: Preserve current exclusion of ignored weights by relying on the existing weight-history endpoint defaults. Preserve cat grouping, date range controls, local language/date formatting, SPA routing, backup format, duration trust semantics, poller behavior, Tuya DP behavior, cat identification, and `/display/summary`.

**Scale/Scope**: Household self-hosted deployment with small-to-moderate visit history per cat. Client-side smoothing is sufficient for the existing dashboard ranges.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Evidence and scope: PASS. Plan cites `docs/AGENTS.md`, `docs/codebase-research.md`, `docs/specs/001-smooth-weight-trend/spec.md`, `frontend/src/components/WeightChart.jsx`, `frontend/src/components/WeightChart.test.jsx`, `frontend/src/api/client.js`, `app/routers/visits.py`, and `app/schemas.py`.
- Runtime and boundaries: PASS. Uses existing React/Recharts frontend boundary and existing API client; no backend-to-frontend dependency or new shared service.
- API compatibility: PASS. Existing HTTP response fields and semantics are preserved; no firmware, webhook, backup, OpenAPI, or display contract changes.
- Database durability: PASS. No schema or persisted data changes; historical measurements remain unchanged.
- Security and secrets: PASS. No new sensitive surfaces or secret handling.
- Observability: PASS. No operational backend failure path is introduced; sparse-data UI behavior remains explicit.
- Tests and gates: PASS. Required frontend lint, focused Vitest chart tests, frontend test suite as feasible, and npm audit are identified.
- Legacy behavior: PASS. Ignored weight exclusion, cat grouping, date ranges, poller, Tuya, duration trust, backup format, SPA fallback, and display contract are preserved.

## Project Structure

### Documentation (this feature)

```text
docs/specs/001-smooth-weight-trend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── weight-chart-contract.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── components/
│   │   ├── WeightChart.jsx
│   │   └── WeightChart.test.jsx
│   ├── api/
│   │   └── client.js
│   └── i18n/
│       └── translations.js
└── package.json

app/
├── routers/
│   └── visits.py
└── schemas.py
```

**Structure Decision**: Implement smoothing inside the chart presentation boundary, likely as helper logic colocated with `WeightChart.jsx` unless task planning decides a small frontend utility is clearer for tests. `app/routers/visits.py` and `app/schemas.py` are evidence for the existing data contract, not planned edit targets.

## Phase 0: Research

Research decisions are recorded in [research.md](./research.md). All technical context is resolved; no `NEEDS CLARIFICATION` markers remain.

## Phase 1: Design and Contracts

Design artifacts:

- [data-model.md](./data-model.md)
- [contracts/weight-chart-contract.md](./contracts/weight-chart-contract.md)
- [quickstart.md](./quickstart.md)

## Constitution Check: Post-Design

- Evidence and scope: PASS. Design artifacts preserve the spec scope and cite existing code contracts.
- Runtime and boundaries: PASS. Design remains frontend-first with no new dependencies.
- API compatibility: PASS. Contract artifact states that `/visits/weight-history` is unchanged.
- Database durability: PASS. Data model is derived/presentation-only; no migration.
- Security and secrets: PASS. No new exposure.
- Observability: PASS. UI states are sufficient for sparse/no-data cases.
- Tests and gates: PASS. Quickstart identifies focused and full frontend verification, including audit.
- Legacy behavior: PASS. Existing backend filters and cat grouping remain authoritative.

## Complexity Tracking

No constitution violations.
