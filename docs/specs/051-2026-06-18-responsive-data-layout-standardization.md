# Responsive Data Layout Standardization

Priority: P1

Implementation scope:
Frontend data-heavy screens and shared table/card styles. This spec standardizes how tables, mobile cards, and stacked rows behave across Visits, Cat detail, and Diagnostics.

## Summary

- Keep dense desktop tables where they help scanning.
- Use deliberate mobile card layouts for high-use operational lists.
- Avoid relying on the global stacked-table fallback for complex rows unless every cell has a correct mobile label.
- Make table/card behavior consistent across Visits, Cat detail, and Diagnostics.

## Problem

The frontend currently mixes two responsive strategies:

- `frontend/src/components/VisitsList.jsx` renders a dedicated desktop table plus dedicated mobile cards.
- `frontend/src/index.css` globally transforms all `.table` elements into stacked mobile rows under `700px`.
- `frontend/src/pages/CatDetail.jsx` and `frontend/src/pages/Diagnostics.jsx` rely more heavily on the global table transformation.

This creates uneven mobile behavior. Some screens get intentionally composed mobile cards, while others inherit generic stacked rows that may be harder to scan, especially when a row contains JSON snippets, action groups, badges, or long notes.

## Current Behavior

- Visits details:
  - desktop table is hidden on mobile.
  - `.visit-card-list` becomes the primary mobile representation.
- Visits summary:
  - has a desktop summary table and a dedicated mobile summary card list.
- Cat detail event history:
  - renders a normal table with `data-label` attributes.
  - relies on the global mobile table transform.
- Diagnostics:
  - renders several tables, including payload-heavy diagnostics events.
  - relies on the global mobile table transform.
- Global CSS changes all `.table`, `.table tbody`, `.table tr`, and `.table td` to block layout on narrow screens.

## Proposed Behavior

Define a clear frontend rule:

- Use desktop tables for dense, repeated, comparable data.
- Use explicit mobile cards for high-use or complex rows.
- Use the global stacked-table fallback only for simple rows with short values and complete `data-label` coverage.

Apply this rule to:

- Visits:
  - preserve current dedicated mobile cards.
  - ensure summary cards and detail cards share spacing, badge, and action treatment.
- Cat detail events:
  - add a dedicated event-card layout for mobile, or tighten the existing stacked rows so actions, notes, shared-cat labels, and birthday rows remain readable.
- Diagnostics:
  - avoid stacked table rows for JSON payloads.
  - use compact diagnostic event cards with collapsible payload previews on mobile.
- Shared CSS:
  - restrict the global stacked-table rule to an opt-in class, for example `.table--stacked-mobile`.
  - add explicit classes for tables that should remain horizontally scrollable or convert to cards.

## Implementation Notes

- Audit every table component/page:
  - `frontend/src/components/VisitsList.jsx`
  - `frontend/src/pages/Visits.jsx`
  - `frontend/src/pages/CatDetail.jsx`
  - `frontend/src/pages/Diagnostics.jsx`
- Move the global `@media (max-width: 700px)` table transformation behind an opt-in class.
- Add mobile card sections only where they improve clarity.
- Keep desktop table column widths stable.
- Ensure mobile card action targets are at least as comfortable as existing buttons.
- Do not introduce a component framework or new CSS methodology.

## Non-Goals

- Do not redesign the data model or APIs.
- Do not remove desktop tables.
- Do not add charts or new analytics.
- Do not change visit aggregation behavior.
- Do not change Diagnostics content; only presentation and disclosure.

## Acceptance Criteria

- Visits desktop and mobile layouts remain functionally unchanged or cleaner.
- Cat detail event history is readable on mobile without relying on awkward table stacking.
- Diagnostics recent events are readable on mobile, including long payloads.
- Global table stacking no longer applies accidentally to every `.table`.
- Every responsive data layout has complete labels or card headings on mobile.
- No mobile row/card requires horizontal scrolling for normal content.
- Desktop tables remain dense and scannable.

## Verification Plan

- Add or update frontend tests for the presence of mobile-card containers where implemented.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manually verify at desktop, tablet, and mobile widths:
  - Visits summary
  - Visits details
  - Cat detail event history
  - Diagnostics open visits
  - Diagnostics recent events
- Check both light and dark themes.

## Rollback Notes

No backend or data change is involved. Rollback restores the prior CSS table behavior and page-level markup.
