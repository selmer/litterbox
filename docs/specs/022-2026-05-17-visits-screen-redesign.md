# Visits Screen Redesign

Priority: P1

Implementation scope:
Frontend Visits page and visit-list presentation. This spec improves visit browsing, filtering, responsive layout, row actions, and correction flows.

## Summary

- Bring the Visits screen up to the dashboard's polish level.
- Improve filter clarity, table/card responsiveness, row actions, reassign flow, delete confirmation, and pagination.
- Keep the existing backend visit APIs.

## Key Changes

- Replace the current loose filter bar with a deliberate segmented/filter control using shared button or filter primitives.
- Keep available filters: All, per-cat, and Unidentified.
- Improve the desktop visit table:
  - stable column widths for cat, started, duration, weight, ID, and actions
  - clear auto/manual/unidentified badges
  - compact action area that does not dominate the row
- Replace mobile pseudo-table rows with compact visit cards or a dedicated mobile row layout.
- Fix action cells on mobile so reassign/delete controls are labelled and visually grouped.
- Improve reassign modal:
  - show visit time, weight, current assignment, and candidate cats clearly
  - keep the visitor/unidentified option visually distinct from active cats
- Improve delete confirmation:
  - avoid expanding table rows awkwardly
  - use a small confirmation modal, popover, or compact confirmation state that remains stable on mobile
- Polish pagination with predictable spacing, disabled states, and concise range text.

## Visual Details

- Visits is an operational history screen, not a dashboard card collection.
- Dense table layout is appropriate on desktop; mobile should prioritize readable cards over forcing table semantics visually.
- Destructive actions should be available but visually secondary until confirmation.
- Keep unidentified visits easy to scan without making the whole page feel alarming.

## Acceptance Criteria

- Desktop Visits shows a clean, stable history table with clear filters and row actions.
- Mobile Visits renders readable visit cards or rows without empty labels, clipped buttons, or horizontal scrolling.
- Reassign works for identified and unidentified visits.
- Delete confirmation is clear and does not cause row layout jumps.
- Loading, fetch error, empty, filtered-empty, and paginated states are handled.
- No backend or API changes are introduced.

## Verification Plan

- Run frontend tests for Visits filtering, pagination, reassign, delete success, and delete/reassign errors.
- Add or update tests for mobile-friendly action rendering if component tests support it.
- Manually verify All, per-cat, and Unidentified filters.
- Manually verify normal rows, unidentified rows, manual rows, empty state, and fetch error state.
- Check desktop, tablet, and mobile widths in both themes.

## Assumptions

- Existing API calls remain `getVisits`, `getCats`, `updateVisit`, and `deleteVisit`.
- Any new UI components should reuse foundation primitives from spec `020`.
- Icon updates should use the icon system from spec `021` when available.
