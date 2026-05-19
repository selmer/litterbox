# 041 - Visits Row Action Menu Cleanup

## Summary
Reduce visual clutter in the full Visits screen by keeping correction work inside the existing edit flow and removing duplicate row actions. Visits should remain useful for correction workflows while keeping each row calm and scannable.

## Key Changes
- Replace the row-level cluster of separate `edit`, `diagnostics`, `reassign`, and `delete` controls with a compact action menu opened from `edit`.
- Keep visit reassignment inside the Edit visit form by changing the Cat field there.
- Remove the separate `reassign` action and modal from the full Visits screen.
- Keep `delete` inside the edit action menu below the edit action.
- Remove the `diagnostics` action from the full Visits screen row/card menu.
- Keep the dedicated Diagnostics page and diagnostics routes unchanged.
- Preserve existing edit and delete behavior, including the delete confirmation modal.

## Public Interfaces
- No backend API changes.
- No database migration.
- Frontend display and interaction cleanup only.

## Test Plan
- Full Visits screen renders a single compact edit action per row/card instead of four side-by-side buttons.
- Opening the edit action exposes `Edit visit` and `Delete` actions.
- The Visits screen no longer shows `diagnostics` or `reassign` actions in row/card menus.
- Changing the Cat field in Edit visit remains the reassignment path.
- Existing edit and delete flows still call the same handlers and modals.
- `VisitsList` component tests cover the grouped action menu.

## Assumptions
- Diagnostics remain accessible through the dedicated Diagnostics page and direct routes, so removing the Visits shortcut does not remove the underlying capability.
- The Visits screen prioritizes operational scanning and correction over diagnostics discovery.
- A separate reassign modal is unnecessary while Edit visit supports changing the visit cat.
