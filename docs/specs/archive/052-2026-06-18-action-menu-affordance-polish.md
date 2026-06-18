# Action Menu Affordance Polish

Priority: P2

Implementation scope:
Frontend action controls in Visits, Cats, Cat detail, and shared UI primitives. This spec improves menu affordance, consistency, and destructive-action treatment without changing the underlying workflows.

## Summary

- Replace ambiguous text-only row menu triggers with a consistent action-menu affordance.
- Keep existing edit, delete, deactivate, reactivate, and diagnostics workflows.
- Improve keyboard, focus, and visual behavior for compact row/card action menus.
- Preserve the prior decision to reduce row clutter.

## Problem

Recent UI cleanup moved repeated row actions into compact menus. That reduced clutter, but the current menu triggers still read like ordinary buttons:

- Visits uses a `details` trigger labeled `Edit`.
- Cats uses a `details` trigger labeled `More`.
- Cat detail event rows use separate `Edit` and `Delete` buttons.

The interaction model is therefore inconsistent. Operators have to learn per-screen action placement, and destructive actions do not always feel clearly separated from routine actions.

## Current Behavior

- `frontend/src/components/VisitsList.jsx`
  - `VisitActions` uses a native `<details>` menu.
  - trigger label is `Edit`.
  - menu can contain `Edit visit`, `Diagnostics`, and `Delete`, depending on props.
- `frontend/src/pages/Cats.jsx`
  - cat rows have visible `View` and `Edit` buttons plus a `More` details menu for deactivate/reactivate.
- `frontend/src/pages/CatDetail.jsx`
  - event rows show visible `Edit` and `Delete` buttons.
- Existing spec `041` intentionally removed duplicate visits row actions and kept correction actions compact.

## Proposed Behavior

Introduce one shared compact action-menu pattern for repeated items:

- Trigger:
  - icon-first button with an accessible label such as `Actions for visit #123` or `Actions for Mochi`.
  - use existing icon system; prefer an ellipsis/menu icon if available.
  - visible text is optional on dense desktop rows, but accessible name is required.
- Menu:
  - routine actions first.
  - navigation actions next.
  - destructive actions separated visually at the bottom.
  - destructive items use danger text, but final destructive confirmation remains in the modal.
- Placement:
  - align menus consistently to the row/card end.
  - avoid clipping inside table containers.
  - support mobile cards without changing layout height unexpectedly.

Apply to:

- Visits detail rows/cards.
- Cats list rows/cards for secondary actions.
- Cat detail event rows/cards.

## Implementation Notes

- Add a small shared component if it reduces duplication, for example `ActionMenu` in `frontend/src/components/ui.jsx` or a new component file.
- If native `<details>` is retained:
  - normalize trigger class, menu class, and danger-item class.
  - ensure summary markers are hidden consistently.
  - ensure focus rings remain visible.
- If a custom menu is introduced:
  - support Escape to close.
  - close on outside click.
  - preserve keyboard access.
  - do not overbuild a general popover library.
- Update translations for accessible labels and action text where needed.

## Non-Goals

- Do not reintroduce multiple always-visible row actions on Visits.
- Do not change backend APIs.
- Do not change the edit/delete/deactivate semantics.
- Do not remove confirmation for destructive actions.
- Do not add bulk actions.

## Acceptance Criteria

- Visits row/card actions use the same trigger style as Cats and Cat detail event actions.
- Menu triggers have clear accessible names.
- Destructive actions are visually separated from routine actions.
- Existing edit, delete, deactivate, reactivate, and diagnostics links still work where currently available.
- Menus work in desktop tables and mobile cards.
- Keyboard focus is visible on trigger and menu items.
- The implementation does not create table overflow or clipping regressions.

## Verification Plan

- Add/update component tests for the shared action menu if introduced.
- Update Visits, Cats, and Cat detail page/component tests for available actions.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manual checks:
  - open and close menus with mouse.
  - tab to menu triggers.
  - verify mobile card action placement.
  - verify destructive confirmation flows still appear before mutation.

## Rollback Notes

No migration or backend change is required. Rollback restores the previous per-screen action controls.
