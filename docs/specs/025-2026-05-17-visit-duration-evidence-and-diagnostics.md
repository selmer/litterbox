# Visit Duration Evidence and Diagnostics

Priority: P0

## Summary

Visit durations are currently too opaque to trust when Tuya completion signals are missed. A hard-timeout fallback can produce durations like 30 minutes, which may look like a real litterbox visit even when the app only knows that reconciliation failed.

This spec adds explicit duration evidence and visit diagnostics so operators can inspect why a duration was chosen, point at the relevant evidence, and avoid counting fallback durations as real time in the box.

## Key Changes

- Add duration metadata to visits:
  - `duration_source`: one of `status_dp`, `report_log_counter`, `report_log_duration`, `manual`, `hard_timeout`, or `unknown`.
  - `duration_is_estimated`: boolean, default `false`.
- Add a `visit_diagnostics` table linked to visits for poller decision history:
  - event type examples: `weight_seen`, `reconciliation_attempt`, `report_logs_fetched`, `completion_matched`, `pending_retry`, `hard_timeout`.
  - compact JSON payload with elapsed seconds, timestamps, strategy, fetched log count, relevant Tuya code/value/time snippets, and sanitized error details.
  - no secrets, API keys, or full cloud credentials.
- Add API support:
  - existing visit responses include `duration_source` and `duration_is_estimated`.
  - `GET /visits/{id}/diagnostics` returns diagnostics for a visit in chronological order.
- Update poller duration handling:
  - status-DP completion stores source `status_dp`.
  - Tuya counter reconciliation stores source `report_log_counter`.
  - Tuya duration-only reconciliation stores source `report_log_duration`.
  - manual visit creation stores source `manual`.
  - hard timeout closes the visit as unresolved fallback, sets source `hard_timeout`, sets `duration_is_estimated=true`, and leaves `duration_seconds=null`.

## Acceptance Criteria

- Future hard-timeout visits do not add fake 1800-second durations to dashboard totals.
- Every future automatically closed visit records enough evidence to explain why it closed and where the duration came from.
- Pending retries and failed Tuya report-log lookups are inspectable after the fact.
- Diagnostics are retrievable by visit id without exposing secrets.
- Existing visits remain readable; historical rows are not automatically repaired in this pass.

## Test Plan

- Migration/model tests:
  - existing visits receive safe default duration metadata.
  - diagnostics can be stored, linked to a visit, and returned chronologically.
- Poller tests:
  - status-DP completion sets `duration_source=status_dp`.
  - report-log counter completion sets `duration_source=report_log_counter`.
  - duration-only completion sets `duration_source=report_log_duration`.
  - pending retry writes diagnostics and keeps the visit open.
  - hard timeout closes the visit with `duration_seconds=null`, `duration_source=hard_timeout`, and `duration_is_estimated=true`.
  - hard-timeout diagnostics include elapsed seconds and reconciliation context.
- API tests:
  - visit list/detail responses include duration metadata.
  - `GET /visits/{id}/diagnostics` returns diagnostics for an existing visit.
  - unknown visit diagnostics request returns 404.
- Run:
  - `python3 -m py_compile app/poller.py app/models.py app/routers/visits.py tests/test_poller.py`
  - `.venv/bin/python -m pytest tests/ -q`

## Assumptions

- This fixes future visits only; existing 30-minute or 5-minute historical rows are left untouched.
- An unresolved visit with unknown real duration is better than storing a fake fallback duration.
- Diagnostics are API/DB-only in this round; UI badges or detail panels can be added later.
- Tuya raw data is summarized into relevant snippets instead of stored wholesale.
