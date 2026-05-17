# Cats Screen Redesign

Priority: P1

Implementation scope:
Frontend Cats page and cat management presentation. This spec improves cat profile rows/cards, photo/avatar consistency, active/inactive states, and edit/deactivate actions.

## Summary

- Bring the Cats screen up to the same visual standard as the dashboard.
- Make cat management feel like profile management rather than a plain settings list.
- Keep the existing backend cat APIs.

## Key Changes

- Redesign each cat item as a compact profile row or card:
  - avatar/photo
  - cat name
  - reference weight
  - active/inactive status
  - created date or secondary metadata
  - edit and deactivate/reactivate actions
- Reuse the same avatar/photo treatment used by dashboard cat summaries.
- Improve the add/edit form presentation using shared form and modal/card styles from spec `020`.
- Make inactive cats visually quieter without making text hard to read.
- Use consistent status badges for inactive and missing reference weight states.
- Improve empty state with a clear `Add cat` action.

## Visual Details

- Cat rows should be scannable at a glance; avoid burying the reference weight in paragraph-like text.
- Actions should be aligned consistently and should not compete with the cat name.
- The add form may remain inline if it feels natural, but it should use the same spacing and action hierarchy as modals/forms elsewhere.
- Photo fallback should match the icon/avatar system from spec `021`.

## Acceptance Criteria

- Cats page presents active and inactive cats with consistent profile-style rows/cards.
- Add, edit, deactivate, and reactivate flows continue to work.
- Cat photo/avatar treatment matches the dashboard.
- Missing reference weight is visible but calm.
- Empty state is compact and includes a direct add action.
- No backend or API changes are introduced.

## Verification Plan

- Run frontend tests for Cats create, edit, deactivate, and reactivate behavior.
- Manually verify cats with and without reference weights.
- Manually verify active and inactive cats.
- Manually verify empty state and add/edit form states.
- Check desktop, tablet, and mobile widths in both themes.

## Assumptions

- Existing API calls remain `getCats`, `createCat`, and `updateCat`.
- Photo upload internals are not redesigned here unless needed for avatar consistency.
- Shared primitives from specs `020` and `021` are available before this spec is implemented.
