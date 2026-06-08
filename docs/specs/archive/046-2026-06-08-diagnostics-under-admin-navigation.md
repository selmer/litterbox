# Diagnostics Under Admin Navigation

## Summary
Move Diagnostics out of the primary application navigation and expose it from the Admin page as an operational tool. Diagnostics remains routable at `/diagnostics` for deep links and contextual links.

## Problem
Diagnostics is useful for maintenance and troubleshooting, but it is too prominent as a top-level navigation item for daily litterbox monitoring. The main navigation should focus on regular workflows: dashboard, visits, cats, and admin.

## Current Behavior
- `frontend/src/App.jsx` shows `Diagnostics` in the sidebar next to daily-use pages.
- `/diagnostics` is a normal route and is linked from visit diagnostics actions.
- `frontend/src/pages/Admin.jsx` does not provide a diagnostics entry point.

## Proposed Behavior
- Remove the Diagnostics link from the primary sidebar navigation.
- Keep the `/diagnostics` route available.
- Add a compact Admin section linking to `/diagnostics`.
- Use existing i18n labels and add admin-specific copy for the section description.
- Preserve contextual links to diagnostics from visit rows.

## Acceptance Criteria
- The sidebar no longer contains a Diagnostics navigation item.
- `/diagnostics` still loads directly.
- Admin contains a clear link to Diagnostics.
- Dutch and English copy render through the translation dictionary.
- Existing diagnostics page and visit diagnostics links keep working.

## Verification Plan
- Add/update frontend tests for sidebar visibility and Admin diagnostics access.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
