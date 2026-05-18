# 026 - Weight History Diagnostics and Mutation Consistency

## Summary

Make weight-chart anomalies traceable and pin down mutation behavior around visit records. The immediate goal is to identify exactly which visit row backs a suspicious chart point after reloads, while regression tests verify that weight-history data responds correctly to delete, unidentified, and reassign operations.

## Problem

A weight point can remain visible in the dashboard chart after an operator believes the related visit entry was changed or removed. Because the chart previously showed only date, cat, and weight, it was difficult to map a suspicious point back to the underlying visit record.

The backend `GET /visits/weight-history` endpoint is expected to be a direct projection of persisted visits: active cats only, non-null `cat_id`, non-null `weight_kg`, and visits inside the requested date range. If a point remains visible after a page reload, the most useful next diagnostic is the exact `visit_id` returned by the endpoint.

## Current Behavior

- `GET /visits/weight-history` returns `visit_id` in each data point.
- The dashboard chart groups points by timestamp and cat name, but the tooltip does not expose `visit_id`.
- The visits API has tests for basic delete/update behavior, but did not explicitly verify weight-history behavior after delete, reassign, or marking a visit unidentified.
- `PATCH /visits/{id}` currently supports cat reassignment only; it does not edit `started_at`, `duration_seconds`, or `weight_kg`.

## Proposed Behavior

### Implemented v1

- Preserve each point's `visit_id` in the frontend chart data model.
- Show `Visit #<id>` in the weight chart tooltip for each hovered point.
- Add backend regression tests for weight-history mutation consistency:
  - deleted visits no longer appear in weight-history
  - visits marked unidentified no longer appear in weight-history
  - reassigned visits move from the old cat series to the new cat series

### Follow-Up Scope

- Add frontend data invalidation so dashboard weight-history refetches immediately after visit delete/reassign/edit actions in the same browser session.
- Add full manual visit edit support if needed:
  - `started_at`
  - `duration_seconds`
  - `weight_kg`
  - derived `ended_at` updates
- Add UI affordances for editing those fields if manual correction becomes part of the visits workflow.

## Acceptance Criteria

- Hovering a dashboard weight-chart point shows the backing visit id.
- The chart still keeps same-day and cross-year points distinct.
- Backend tests prove deleted visits are absent from `/visits/weight-history`.
- Backend tests prove unidentified visits are absent from `/visits/weight-history`.
- Backend tests prove reassigned visits move to the reassigned cat series.
- No API contract change is required, because `visit_id` was already present in weight-history data points.

## Verification

- `.venv/bin/python -m py_compile app/routers/visits.py tests/test_api_visits.py`
- `.venv/bin/python -m pytest tests/test_api_visits.py -q`
- Frontend targeted test for `WeightChart`
- `npm run lint`
- `git diff --check`

## Rollback Notes

This change is diagnostic and test-only at the data layer. Rolling back the frontend tooltip change removes the visible visit id but does not affect backend data or migrations.

## Assumptions

- A chart point that remains after a full reload still exists in backend weight-history data.
- The next useful debugging artifact is the exact visit id behind the visible point.
- Full visit field editing is intentionally deferred until we confirm which persisted record is incorrect.
