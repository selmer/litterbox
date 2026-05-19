# 041 - Visits Row Action Menu Cleanup

## Summary
Reduce visual clutter in the full Visits screen by grouping secondary row actions under the existing edit control and removing the diagnostics shortcut from this menu. Visits should remain useful for correction workflows while keeping each row calm and scannable.

## Key Changes
- Replace the row-level cluster of separate `edit`, `diagnostics`, `reassign`, and `delete` controls with a compact action menu opened from `edit`.
- Move `reassign` and `delete` into that menu below the edit action.
- Remove the `diagnostics` action from the full Visits screen row/card menu.
- Keep the dedicated Diagnostics page and diagnostics routes unchanged.
- Preserve existing edit, reassign, and delete behavior, including the delete confirmation modal.

## Public Interfaces
- No backend API changes.
- No database migration.
- Frontend display and interaction cleanup only.

## Test Plan
- Full Visits screen renders a single compact edit action per row/card instead of four side-by-side buttons.
- Opening the edit action exposes `Edit visit`, `Reassign`, and `Delete` actions.
- The Visits screen no longer shows a `diagnostics` action in row/card menus.
- Existing edit, reassign, and delete flows still call the same handlers and modals.
- `VisitsList` component tests cover the grouped action menu.

## Assumptions
- Diagnostics remain accessible through the dedicated Diagnostics page and direct routes, so removing the Visits shortcut does not remove the underlying capability.
- The Visits screen prioritizes operational scanning and correction over diagnostics discovery.
