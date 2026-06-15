# Visits Partial Period Averages

Priority: P1

Implementation scope:
Backend Visits summary aggregation and backend tests. This spec corrects per-day averages for the current week and current month in the Visits aggregate history view.

## Summary

- Change `average_visits_per_day` for the current week to divide by elapsed local days in the week instead of 7.
- Change `average_visits_per_day` for the current month to divide by elapsed local days in the month instead of the full month length.
- Keep completed weeks and months comparable by dividing them by their full bucket length.
- Keep the API response shape and frontend display unchanged.

## Problem

The Visits screen's weekly and monthly aggregate views currently divide visit totals by the full bucket duration. This makes the current week and current month look artificially low early in the period.

Example: if the current week has only just started and there has been 1 visit, the weekly view shows `0.14/day` because it divides by 7 days. For an in-progress week, the more useful operational number is the average over days that have actually elapsed in the current local week.

The same issue applies to the current month: dividing by 30 or 31 days early in the month produces a number that is not meaningful for current household activity.

## Current Behavior

- `app/routers/visits.py` computes `average_visits_per_day` in `visit_summary` with `round(len(visits) / _bucket_days(bucket_start, bucket_end), 2)`.
- `_bucket_days` divides by the full duration between `bucket_start` and `bucket_end`.
- Weekly buckets therefore divide by 7 days, including the current week.
- Monthly buckets divide by the full month length, including the current month.
- Frontend display in `frontend/src/pages/Visits.jsx` renders this value as `{count}/day` for week and month modes.

## Proposed Behavior

Compute the average denominator based on whether the bucket is complete or still in progress:

- `day`: always divide by `1`.
- completed `week`: divide by `7`.
- current `week`: divide by elapsed local calendar days from Monday through today, inclusive.
- completed `month`: divide by the number of local calendar days in that month.
- current `month`: divide by elapsed local calendar days from the 1st through today, inclusive.

Examples:

- Current week is Wednesday and the week has 1 visit: `1 / 3 = 0.33/day`.
- Completed week has 1 visit: `1 / 7 = 0.14/day`.
- Current month is the 10th and the month has 5 visits: `5 / 10 = 0.5/day`.
- Completed 31-day month has 31 visits: `31 / 31 = 1.0/day`.

## Implementation Notes

- Add a helper in `app/routers/visits.py`, for example `_average_denominator_days(bucket_start, bucket_end, bucket, now)`.
- Compute `now = datetime.now(timezone.utc)` once in `visit_summary` and pass it into the helper.
- Use existing timezone helpers:
  - normalize `now` with `as_utc(now).astimezone(app_timezone())`;
  - compare bucket starts in local time;
  - keep ISO week behavior with Monday as week start, matching the existing `_bucket_start` logic.
- Replace the existing `_bucket_days(bucket_start, bucket_end)` usage for `average_visits_per_day` with the new denominator helper.
- Keep rounding unchanged: `round(len(visits) / denominator_days, 2)`.
- Keep response schema unchanged; do not add new fields.
- Keep frontend copy unchanged; `x/day` remains the display format.

## Non-Goals

- Do not change bucket boundaries.
- Do not change `visit_count`, `identified_visit_count`, `unidentified_visit_count`, duration averages, or weight averages.
- Do not change frontend UI or translations.
- Do not change health signal calculations; this only affects `/visits/summary`.
- Do not add persisted summary tables.

## Acceptance Criteria

- Current weekly buckets divide by elapsed local week days including today.
- Completed weekly buckets still divide by 7.
- Current monthly buckets divide by elapsed local month days including today.
- Completed monthly buckets divide by the full number of days in that month.
- Local timezone behavior matches the app's existing `Europe/Amsterdam` default and `APP_TIMEZONE` support.
- API response shape for `GET /visits/summary` is unchanged.
- The Visits page continues to render the returned `average_visits_per_day` without frontend changes.

## Verification Plan

- Add backend tests in `tests/test_api_visits.py` for:
  - current week on Wednesday with 1 visit returns `0.33`.
  - completed week with 1 visit returns `0.14`.
  - current month on the 10th with 5 visits returns `0.5`.
  - completed month uses the full month length.
- Prefer direct helper tests with an explicit `now` argument to avoid fragile global datetime monkeypatching.
- Run:
  - `.venv/bin/python -m pytest tests/test_api_visits.py`
  - `.venv/bin/python -m py_compile app/routers/visits.py`
- Optional smoke check:
  - `DATABASE_URL=sqlite:////tmp/litterbox-route-smoke.db .venv/bin/python -c "from app.main import app"`

## Rollback Notes

No migration or data change is required. Rolling back restores the previous full-bucket denominator behavior immediately.
