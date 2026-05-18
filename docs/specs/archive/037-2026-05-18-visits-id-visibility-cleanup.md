# 037 - Visits ID Visibility Cleanup

## Summary
Keep visit IDs available on the full Visits screen for debugging and correction workflows, but remove visible visit IDs from the Dashboard recent visits view. The dashboard should stay calm and scannable, while the detailed visits workflow keeps the identifiers operators need.

## Key Changes
- Hide visit IDs in the Dashboard "Recent visits" view.
- Keep visit IDs visible in the full Visits screen.
- Do not change backend APIs, visit schemas, or stored data.
- Preserve existing visit ordering and navigation behavior.

## Public Interfaces
- No API changes.
- No database migration.
- Frontend display-only behavior changes.

## Test Plan
- Dashboard recent visits renders cat, started time, duration, weight, and source/status without a visible ID.
- Full Visits screen still renders visit IDs such as `#73`.
- Existing visit list tests remain green.

## Assumptions
- Visit IDs are still needed for diagnostics and manual correction.
- The Dashboard recent visits view is intended for quick scanning, not debugging.
