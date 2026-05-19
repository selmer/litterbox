# 043 - Cat Deactivation Action De-emphasis

## Summary
Make cat deactivation/reactivation less prominent on the Cats screen because it is a rare management action. The primary cat card actions should stay focused on everyday use: viewing and editing a cat profile.

## Key Changes
- Remove `Deactivate` / `Reactivate` as visible primary buttons from each cat profile card.
- Add a compact secondary action menu to each cat profile card:
  - English trigger: `More`
  - Dutch trigger: `Meer`
- Put the rare status action inside that menu:
  - active cat: `Deactivate` / `Deactiveren`
  - inactive cat: `Reactivate` / `Heractiveren`
- Preserve the existing behavior and API call: `updateCat(cat.id, { active: !cat.active })`.
- Preserve existing success/error toast behavior and active/inactive badges.
- Style the menu to match the compact secondary action menus already used in Visits.

## Public Interfaces
- No backend API changes.
- No database migration.
- Frontend display and interaction cleanup only.
- Adds translation keys for `More` / `Meer` if they do not already exist.

## Test Plan
- Cats page no longer shows `Deactivate` as a prominent primary row action for active cats.
- Cats page shows a `More` menu per cat profile card.
- Active cat menu contains `Deactivate` and clicking it calls `updateCat(id, { active: false })`.
- Inactive cat menu contains `Reactivate` and clicking it calls `updateCat(id, { active: true })`.
- Existing error toasts still render when deactivation/reactivation fails.
- Dutch UI can render `Meer`, `Deactiveren`, and `Heractiveren` through the translation dictionary.

## Assumptions
- No confirmation modal is added in this pass.
- Inactive cats remain visible as they are today.
- `View` and `Edit` remain visible primary actions.
