# Litterbox Improvement Specifications

Generated from a repository assessment on 2026-05-16. This document is a specification index only; it does not authorize implementation without an explicit follow-up request.

Individual improvement specifications now live in `docs/specs/`. That directory is the canonical location for feature and improvement specs.

## Assessment Scope

Reviewed backend, frontend, tests, deployment scripts, migrations, and existing documentation. Key source areas inspected:

- Backend: `app/main.py`, `app/poller.py`, `app/models.py`, `app/schemas.py`, `app/routers/*`
- Frontend: `frontend/src/App.jsx`, `frontend/src/pages/*`, `frontend/src/components/*`, `frontend/src/api/client.js`
- Operations: `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `requirements.txt`, `frontend/package.json`
- Tests and docs: `tests/*`, `frontend/src/**/*.test.jsx`, `README.md`, `docs/*`

Verification could not be executed during the original assessment because `pytest`, `npm`, and `docker` were not installed, and the default command sandbox could not start because `bubblewrap` was unavailable.

## Specification-First Working Rule

No application code change should be made unless a written specification exists first. For this repository, an implementation-ready specification should include:

- Problem statement and affected users/operators.
- Current behavior with file references.
- Proposed behavior.
- Data model, API, UI, and configuration impacts, if any.
- Acceptance criteria.
- Verification plan.
- Rollback or migration notes when runtime data can be affected.

## Specification Index

| # | Specification | Priority |
|---|---|---|
| 001 | [Pydantic v2 Config Deprecation Cleanup](specs/001-2026-05-16-pydantic-v2-config-deprecation-cleanup.md) | P2 |
| 002 | [Frontend Lint Gate Cleanup](specs/002-2026-05-16-frontend-lint-gate-cleanup.md) | P1 |
| 003 | [Frontend Dependency Audit Cleanup](specs/003-2026-05-16-frontend-dependency-audit-cleanup.md) | P1 |
| 004 | [Local npm Global Config Warning Cleanup](specs/004-2026-05-16-local-npm-global-config-warning-cleanup.md) | P2 |
| 005 | [Accurate Runtime Health and Poller Status](specs/005-2026-05-16-accurate-runtime-health-and-poller-status.md) | P0 |
| 006 | [Durable Poller State and Restart Recovery](specs/006-2026-05-16-durable-poller-state-and-restart-recovery.md) | P0 |
| 007 | [API Domain Validation and Referential Integrity](specs/007-2026-05-16-api-domain-validation-and-referential-integrity.md) | P1 |
| 008 | [Safe and Durable Cat Photo Storage](specs/008-2026-05-16-safe-and-durable-cat-photo-storage.md) | P1 |
| 009 | [Deterministic and Scalable Dashboard Queries](specs/009-2026-05-16-deterministic-and-scalable-dashboard-queries.md) | P1 |
| 010 | [Time-Series Weight Chart Correctness](specs/010-2026-05-16-time-series-weight-chart-correctness.md) | P1 |
| 011 | [Frontend Data Fetching, Error States, and Freshness](specs/011-2026-05-16-frontend-data-fetching-error-states-and-freshness.md) | P1 |
| 012 | [Deployment and Release Pipeline Hardening](specs/012-2026-05-16-deployment-and-release-pipeline-hardening.md) | P1 |
| 013 | [Documentation and Test Coverage Trustworthiness](specs/013-2026-05-16-documentation-and-test-coverage-trustworthiness.md) | P2 |
| 014 | [Tuya Excretion Log Reconciliation](specs/014-2026-05-16-tuya-excretion-log-reconciliation.md) | P0 |
| 015 | [Light Professional Dashboard Theme](specs/015-2026-05-16-light-professional-dashboard-theme.md) | P1 |
| 016 | [Dark Elegant Dashboard Theme](specs/016-2026-05-16-dark-elegant-dashboard-theme.md) | P1 |
| 017 | [Future Dashboard Design Enhancements](specs/017-2026-05-16-future-dashboard-design-enhancements.md) | P2 |
