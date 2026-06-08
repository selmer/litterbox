# Local Day Boundary for Today Metrics

## Summary
Dashboard and display metrics labelled as "today" should use the operator's local calendar day instead of UTC midnight. The app stores timestamps in UTC, but user-facing daily counts should match the date shown in the browser and the household's local expectation.

## Problem
When the app runs for a household in Europe/Amsterdam, visits between local midnight and UTC midnight are counted inconsistently:

- Recent visits show timestamps in the browser's local time.
- Dashboard cat cards count `visits_today` from 00:00 UTC.
- The e-paper display summary uses the same UTC day boundary.

This can make the dashboard say a cat visited once today while the recent visit list shows several visits since local midnight.

## Current Behavior
- `app/routers/dashboard.py` uses `datetime.now(timezone.utc)` and derives `today_start` with `now.replace(hour=0, minute=0, second=0, microsecond=0)`.
- Dashboard queries then filter `Visit.started_at >= today_start` and `CleaningCycle.started_at >= today_start`.
- `app/routers/display.py` has `_today_start(now)` with the same UTC-midnight behavior.
- `frontend/src/pages/Dashboard.jsx` fetches recent visits with `getVisits({ limit: 10 })`.
- `frontend/src/components/VisitsList.jsx` renders `new Date(visit.started_at)`, so timestamps are displayed in browser-local time.

## Proposed Behavior
- Define one backend helper for the start of the current local day.
- The default local timezone should be `Europe/Amsterdam`.
- The helper should:
  - Take a timezone-aware UTC `now`.
  - Convert it to the configured local timezone.
  - Replace the local time with `00:00:00.000000`.
  - Convert that local midnight back to UTC for database filtering.
- Use this helper for all user-facing "today" aggregates:
  - Dashboard per-cat `visits_today`.
  - Dashboard per-cat `time_in_box_today_seconds`.
  - Dashboard `unidentified_visits_today`.
  - Dashboard `cleaning_cycles_today`.
  - Display summary `today.visits`.
  - Display summary `today.time_in_box_seconds`.
  - Display summary `today.cleaning_cycles`.
  - Display summary `today.unidentified_visits`.
  - Display per-cat `visits_today`.
- Keep stored timestamps and API timestamp serialization in UTC.
- Keep recent visits sorting and rendering unchanged.

## Configuration
- Add a small application setting for the local timezone, for example `APP_TIMEZONE`.
- Default it to `Europe/Amsterdam`.
- Invalid timezone values should fail clearly at startup or fall back with an explicit logged warning. Prefer failing clearly if startup validation already has a suitable place.

## Non-Goals
- Do not migrate stored visit or cleaning-cycle timestamps.
- Do not change poller timestamp collection.
- Do not change `/visits` ordering or pagination.
- Do not make the frontend responsible for filtering dashboard "today" data.
- Do not add per-user timezones; this app currently behaves like a single-household system.

## Acceptance Criteria
- A visit at `2026-06-07T22:30:00Z` counts as today when local date is `2026-06-08` in `Europe/Amsterdam`.
- A visit at `2026-06-07T21:30:00Z` does not count as today when local date is `2026-06-08` in `Europe/Amsterdam`.
- Dashboard cat cards, dashboard unidentified count, and dashboard cleaning-cycle count all use the same local-day boundary.
- Display summary and display per-cat summaries use the same local-day boundary as the dashboard.
- Recent visits still show the latest visits by absolute timestamp and remain displayed in browser-local time.
- Existing UTC storage behavior remains intact.
- Daylight saving transitions are handled by the timezone database rather than fixed offsets.

## Verification Plan
- Add backend unit tests for the local-day helper around Europe/Amsterdam summer time and winter time.
- Add dashboard API tests covering visits and cleaning cycles between local midnight and UTC midnight.
- Add display API tests covering the same boundary for summary and per-cat counts.
- Run `python3 -m pytest tests/test_api_dashboard.py tests/test_api_display.py`.
- Optionally run the full backend test suite if the local environment allows it.

## Rollback Notes
No data migration is required. Rolling back restores UTC-midnight "today" calculations immediately. Counts may shift back by one or two hours depending on the local timezone and daylight saving offset.
