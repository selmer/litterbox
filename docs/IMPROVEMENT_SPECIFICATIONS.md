# Litterbox Improvement Specifications

Generated from a repository assessment on 2026-05-16. This document is a specification index only; it does not authorize implementation without an explicit follow-up request.

Individual improvement specifications now live in `docs/specs/`. That directory is the canonical location for active feature and improvement specs. Built specs move to `docs/specs/archive/` as the final cleanup step after implementation.

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

After a spec is implemented and verified, move it from `docs/specs/` to `docs/specs/archive/` and update this index link.

## Specification Index

| # | Specification | Priority |
|---|---|---|
| 001 | [Pydantic v2 Config Deprecation Cleanup](specs/archive/001-2026-05-16-pydantic-v2-config-deprecation-cleanup.md) | P2 |
| 002 | [Frontend Lint Gate Cleanup](specs/archive/002-2026-05-16-frontend-lint-gate-cleanup.md) | P1 |
| 003 | [Frontend Dependency Audit Cleanup](specs/archive/003-2026-05-16-frontend-dependency-audit-cleanup.md) | P1 |
| 004 | [Local npm Global Config Warning Cleanup](specs/archive/004-2026-05-16-local-npm-global-config-warning-cleanup.md) | P2 |
| 005 | [Accurate Runtime Health and Poller Status](specs/archive/005-2026-05-16-accurate-runtime-health-and-poller-status.md) | P0 |
| 006 | [Durable Poller State and Restart Recovery](specs/archive/006-2026-05-16-durable-poller-state-and-restart-recovery.md) | P0 |
| 007 | [API Domain Validation and Referential Integrity](specs/archive/007-2026-05-16-api-domain-validation-and-referential-integrity.md) | P1 |
| 008 | [Safe and Durable Cat Photo Storage](specs/archive/008-2026-05-16-safe-and-durable-cat-photo-storage.md) | P1 |
| 009 | [Deterministic and Scalable Dashboard Queries](specs/archive/009-2026-05-16-deterministic-and-scalable-dashboard-queries.md) | P1 |
| 010 | [Time-Series Weight Chart Correctness](specs/archive/010-2026-05-16-time-series-weight-chart-correctness.md) | P1 |
| 011 | [Frontend Data Fetching, Error States, and Freshness](specs/archive/011-2026-05-16-frontend-data-fetching-error-states-and-freshness.md) | P1 |
| 012 | [Deployment and Release Pipeline Hardening](specs/archive/012-2026-05-16-deployment-and-release-pipeline-hardening.md) | P1 |
| 013 | [Documentation and Test Coverage Trustworthiness](specs/archive/013-2026-05-16-documentation-and-test-coverage-trustworthiness.md) | P2 |
| 014 | [Tuya Excretion Log Reconciliation](specs/archive/014-2026-05-16-tuya-excretion-log-reconciliation.md) | P0 |
| 015 | [Light Professional Dashboard Theme](specs/archive/015-2026-05-16-light-professional-dashboard-theme.md) | P1 |
| 016 | [Dark Elegant Dashboard Theme](specs/archive/016-2026-05-16-dark-elegant-dashboard-theme.md) | P1 |
| 017 | [Future Dashboard Design Enhancements](specs/archive/017-2026-05-16-future-dashboard-design-enhancements.md) | P2 |
| 018 | [ESP32 E-Paper Display View](specs/archive/018-2026-05-16-esp32-epaper-display-view.md) | P1 |
| 019 | [UI Review Remediation Roadmap](specs/archive/019-2026-05-17-ui-review-remediation-roadmap.md) | P1 |
| 020 | [UI Foundation Polish Pass](specs/archive/020-2026-05-17-ui-foundation-polish-pass.md) | P1 |
| 021 | [Navigation and Icon System](specs/archive/021-2026-05-17-navigation-and-icon-system.md) | P1 |
| 022 | [Visits Screen Redesign](specs/archive/022-2026-05-17-visits-screen-redesign.md) | P1 |
| 023 | [Cats Screen Redesign](specs/archive/023-2026-05-17-cats-screen-redesign.md) | P1 |
| 024 | [Chart and Dashboard Refinement](specs/archive/024-2026-05-17-chart-and-dashboard-refinement.md) | P2 |
| 025 | [Visit Duration Evidence and Diagnostics](specs/archive/025-2026-05-17-visit-duration-evidence-and-diagnostics.md) | P0 |
| 026 | [Weight History Diagnostics and Mutation Consistency](specs/archive/026-2026-05-17-weight-history-diagnostics-and-mutation-consistency.md) | P1 |
| 027 | [Visit ID UI Consistency](specs/archive/027-2026-05-17-visit-id-ui-consistency.md) | P2 |
| 028 | [E-Paper Weight Comparison Display](specs/archive/028-2026-05-17-epaper-weight-comparison-display.md) | P1 |
| 029 | [Visit Correction Workflow](specs/029-2026-05-17-visit-correction-workflow.md) | P0 |
| 030 | [Weight Trend Confidence](specs/030-2026-05-17-weight-trend-confidence.md) | P0 |
| 031 | [Cat Health Signals](specs/031-2026-05-17-cat-health-signals.md) | P1 |
| 032 | [Device and Data Diagnostics Screen](specs/032-2026-05-17-device-and-data-diagnostics-screen.md) | P1 |
| 033 | [E-Paper Display Profiles](specs/033-2026-05-17-epaper-display-profiles.md) | P2 |
| 034 | [Early Cat Identification and Match Diagnostics](specs/archive/034-2026-05-18-early-cat-identification-and-match-diagnostics.md) | P1 |
| 035 | [Cat Lifecycle Events and Birthdays](specs/archive/035-2026-05-18-cat-lifecycle-events-and-birthdays.md) | P1 |
| 036 | [Trusted Duration and Adaptive Visit Polling](specs/archive/036-2026-05-18-trusted-duration-and-adaptive-visit-polling.md) | P0 |
| 037 | [Visits ID Visibility Cleanup](specs/archive/037-2026-05-18-visits-id-visibility-cleanup.md) | P2 |
| 038 | [OpenAPI and Swagger Documentation](specs/038-2026-05-18-openapi-and-swagger-documentation.md) | P2 |
| 039 | [Backup and Restore](specs/039-2026-05-18-backup-and-restore.md) | P1 |
| 040 | [E-Paper Two-Cat Label Overlap Polish](specs/040-2026-05-18-epaper-two-cat-label-overlap-polish.md) | P1 |
