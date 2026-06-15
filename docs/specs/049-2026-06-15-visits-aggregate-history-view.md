# Visits Aggregate History View

Priority: P1

Implementation scope:
Backend Visits API, frontend Visits page, API client, translations, and tests. This spec adds daily, weekly, and monthly aggregate views so operators can scan visit history without scrolling through every individual visit.

## Summary

- Add a compact aggregate mode to the Visits screen.
- Default the Visits screen to one row/card per local day.
- Keep the existing detailed visit list available for corrections and diagnostics.
- Compute aggregate buckets in the backend/database, not in the browser.
- Avoid loading the full visit history into React.

## Problem

The Visits screen currently shows individual visits in reverse chronological order. This is useful for audit and correction work, but it becomes scroll-heavy during normal use because every litterbox entry receives its own row or card.

The operator usually wants to answer broader questions first:

- Did every cat visit today?
- Is one cat visiting less or more than usual?
- How many unidentified visits happened recently?
- What is the average visit frequency per week or month?

Showing every individual visit first makes those questions slower to answer. Moving aggregation into the frontend would reduce visible rows, but it would require fetching many or all visits, which risks poor performance as history grows.

## Current Behavior

- `frontend/src/pages/Visits.jsx` fetches `/visits` through `getVisits`.
- `frontend/src/api/client.js` exposes `getVisits({ limit, offset, catId, unidentified, signal })`.
- `app/routers/visits.py` implements `GET /visits` with `limit`, `offset`, `cat_id`, and `unidentified`.
- `GET /visits` returns individual `VisitOut` records ordered by `Visit.started_at.desc()`.
- The page fetches `PAGE_SIZE + 1` visits to determine whether a next page exists.
- `frontend/src/components/VisitsList.jsx` renders a desktop table and mobile cards.
- `app/models.py` already has indexes on `Visit.started_at`, `Visit.cat_id`, and `(Visit.cat_id, Visit.started_at)`.

## Proposed Behavior

Add a view-mode control to the Visits page:

- `Per day`:
  - Default mode.
  - Shows one aggregate row/card per local calendar day.
  - Supports expanding or opening a day to inspect the underlying individual visits.
- `Per week`:
  - Shows one aggregate row/card per local calendar week.
  - Focuses on total visits and per-day averages.
- `Per month`:
  - Shows one aggregate row/card per local calendar month.
  - Focuses on trend-level totals and per-day averages.
- `Details`:
  - Keeps the existing paginated individual visit list.
  - Keeps existing edit and delete workflows.

The active cat filter should apply consistently to all modes:

- `All` includes every visit.
- Per-cat filters include only visits for that cat.
- `Unidentified` includes only visits where `cat_id` is null.

## Backend API

Add a new endpoint:

`GET /visits/summary`

Query parameters:

- `bucket`: `day`, `week`, or `month`; default `day`.
- `limit`: number of buckets to return; default `50`, maximum `500`.
- `offset`: bucket offset; default `0`.
- `cat_id`: optional cat filter.
- `unidentified`: optional unidentified-only filter.
- `from_date`: optional inclusive range start.
- `to_date`: optional inclusive range end.

Response shape:

```json
[
  {
    "bucket": "day",
    "bucket_start": "2026-06-15T00:00:00+02:00",
    "bucket_end": "2026-06-16T00:00:00+02:00",
    "visit_count": 6,
    "identified_visit_count": 5,
    "unidentified_visit_count": 1,
    "average_visits_per_day": 6.0,
    "average_duration_seconds": 83,
    "latest_visit_at": "2026-06-15T18:42:00Z",
    "cats": [
      {
        "cat_id": 1,
        "cat_name": "Plurk",
        "visit_count": 3,
        "average_duration_seconds": 78,
        "average_weight_kg": 3.82,
        "latest_visit_at": "2026-06-15T18:42:00Z"
      }
    ]
  }
]
```

Notes:

- `bucket_start` and `bucket_end` should represent the configured local timezone boundary.
- Stored visit timestamps remain UTC.
- Date filtering should convert local bucket boundaries to UTC before filtering.
- For weekly buckets, use the household-local week definition. Prefer ISO weeks starting Monday unless an existing app convention says otherwise.
- `average_duration_seconds` should only include trusted visible durations, using the same duration trust rules as `VisitOut`.
- `average_weight_kg` should exclude ignored weights by default.
- Empty buckets are not required in the first implementation.

## Performance Requirements

Aggregate rows must be computed by the backend using bounded database queries. The frontend must not fetch all individual visits and group them in memory.

The first implementation should use live SQL aggregation, constrained by:

- `limit` and `offset` over buckets.
- Optional date ranges.
- Existing indexed filters on `started_at` and `cat_id`.
- A default range cap when no explicit range is supplied:
  - `day`: latest 180 days.
  - `week`: latest 104 weeks.
  - `month`: latest 60 months.

If live aggregation proves slow in production, a later spec may introduce a persisted summary table. Do not introduce summary persistence in this first implementation unless profiling shows it is necessary.

## Implementation Notes

- Add Pydantic schemas for:
  - `VisitSummaryBucketOut`
  - `VisitSummaryCatOut`
  - a bucket literal type if useful.
- Keep `/visits` unchanged for detailed history and correction flows.
- Add `getVisitSummary` to `frontend/src/api/client.js`.
- Add a new aggregate list component or keep it inside `Visits.jsx` if the first implementation stays compact.
- Reuse existing loading, error, empty, filter, and pagination patterns from the current Visits page.
- The aggregate endpoint must work under both PostgreSQL and SQLite test environments.
- Because date truncation differs between PostgreSQL and SQLite, prefer a small backend helper that chooses the correct SQL expression per dialect, or fetch only bounded bucket keys and aggregate with database-level grouping where practical.
- Do not compute aggregate buckets from an unbounded ORM `.all()` result.

## Frontend UX

The Visits page should feel like an operational history screen, not a dashboard landing page.

Aggregate row/card content:

- bucket label, such as `Today`, `Yesterday`, `15 Jun`, `Week 25`, or `June 2026`
- total visit count
- unidentified count when nonzero
- per-cat visit counts
- average visits per day for week/month modes
- latest visit time
- an affordance to view details for that bucket

Interactions:

- Switching mode resets pagination to the first page.
- Switching cat/unidentified filter resets pagination to the first page.
- Opening a daily bucket should show the visits for that day, either inline or by switching to Details with a date range filter.
- Editing or deleting an individual visit should refresh the active aggregate data after success.

Desktop:

- Use a dense table or table-like layout with stable columns.
- Keep per-cat counts scannable without making the row too tall.

Mobile:

- Use compact cards.
- Avoid horizontal scrolling.
- Keep action targets large enough for touch.

## Non-Goals

- Do not remove the individual visits list.
- Do not remove edit/delete/correction actions.
- Do not add charts in this spec.
- Do not add a persisted summary/materialized table in the initial implementation.
- Do not migrate existing visit data.
- Do not make the frontend responsible for long-range aggregation.
- Do not change poller visit detection or cat identification logic.

## Acceptance Criteria

- Visits defaults to `Per day` mode.
- `Details` mode preserves the existing individual visits behavior, pagination, filters, edit, and delete.
- `Per day` shows at most one aggregate row/card per local calendar day.
- `Per week` shows weekly buckets with total visits and average visits per day.
- `Per month` shows monthly buckets with total visits and average visits per day.
- All aggregate modes respect All, per-cat, and Unidentified filters.
- Aggregate pagination pages through buckets, not individual visits.
- Aggregate data is returned by `GET /visits/summary`.
- The frontend does not fetch all visits to compute aggregate rows.
- Backend aggregation has bounded default ranges when the client does not provide a range.
- Local day/week/month boundaries match the app timezone behavior from the local-day metrics work.
- Empty, loading, error, and filtered-empty states are handled in all modes.
- Editing or deleting a visit refreshes visible aggregate data.

## Verification Plan

- Add backend API tests for `GET /visits/summary`:
  - daily grouping
  - weekly grouping
  - monthly grouping
  - per-cat filter
  - unidentified filter
  - trusted-duration averaging
  - ignored-weight exclusion
  - local timezone day boundary
  - pagination by bucket
- Add frontend API-client tests or page tests for:
  - default mode is `Per day`
  - switching modes calls the summary or detail endpoint as appropriate
  - filters are passed through in aggregate modes
  - pagination resets on mode/filter changes
  - Details mode still supports edit and delete
- Run:
  - `python3 -m pytest tests/test_api_visits.py`
  - frontend Visits tests with the repository's standard npm test command
- Manually verify desktop and mobile layouts for:
  - All visits
  - a single cat
  - unidentified visits
  - empty result
  - a day with multiple cats
  - a day with only unidentified visits

## Rollback Notes

No data migration is required. Rolling back can remove the summary endpoint and frontend mode control while leaving existing `/visits` behavior intact.
