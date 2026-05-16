# Deterministic and Scalable Dashboard Queries

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
