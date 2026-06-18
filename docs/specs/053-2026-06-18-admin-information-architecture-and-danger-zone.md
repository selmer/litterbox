# Admin Information Architecture and Danger Zone

Priority: P1

Implementation scope:
Frontend Admin page, copy/translations, and tests. This spec separates routine preferences, operational tools, backup, and destructive restore actions into clearer Admin sections.

## Summary

- Make Admin easier to scan by grouping related tools.
- Separate low-risk settings from data-management actions.
- Give restore a clearer danger-zone treatment.
- Keep backup and restore APIs unchanged.

## Problem

The Admin page currently presents language selection, diagnostics, backup download, and restore upload in one two-column card grid. This makes the page compact, but it flattens risk levels:

- changing language is low risk.
- opening Diagnostics is navigational.
- downloading a backup is safe and routine.
- restoring a backup can overwrite application data.

The restore flow has validation and confirmation, but visually it sits at the same hierarchy level as ordinary settings. Operators should be able to immediately see which actions are safe and which require caution.

## Current Behavior

- `frontend/src/pages/Admin.jsx` renders `admin-layout` as a two-column grid.
- Sections:
  - language
  - operational tools link to Diagnostics
  - create backup
  - restore backup
- Restore flow:
  - choose zip file
  - validate archive
  - show validation summary
  - require confirmation checkbox
  - enable restore button
- Backend backup/restore behavior is covered by existing spec `039`.

## Proposed Behavior

Reorganize Admin into clear bands or grouped sections:

- Preferences:
  - language selector.
- Operations:
  - Diagnostics link and any future maintenance links.
- Backup:
  - safe download action.
  - short metadata/copy explaining what is included.
- Danger zone:
  - restore workflow.
  - stronger visual boundary and warning copy.
  - validation summary remains visible before confirmation.

Restore should feel intentionally gated:

- file picker first.
- validation result second.
- confirmation checkbox near the final action.
- final restore button visually destructive.
- copy should explain that restore replaces current app data, without being alarmist.

## Implementation Notes

- Keep `createBackup`, `validateRestoreArtifact`, and `restoreBackup` calls unchanged.
- Update Admin markup and CSS classes in:
  - `frontend/src/pages/Admin.jsx`
  - `frontend/src/App.css`
- Add or update English and Dutch translations in `frontend/src/i18n/translations.js`.
- Consider section headings that are visible and scannable:
  - `Preferences`
  - `Operations`
  - `Backup`
  - `Danger zone`
- Avoid nested cards. Use page sections or cards as top-level surfaces only.
- Keep mobile layout single-column.

## Non-Goals

- Do not change backup archive format.
- Do not change restore validation semantics.
- Do not add scheduled backups.
- Do not add role-based access control.
- Do not move Diagnostics back into primary navigation.
- Do not implement new backend endpoints.

## Acceptance Criteria

- Admin visually separates preferences, operations, backup, and restore.
- Restore appears in a distinct danger-zone section.
- Backup remains easy to find and is not styled as dangerous.
- Restore cannot be submitted without a valid archive and explicit confirmation.
- Validation metadata remains readable.
- Mobile layout remains single-column and readable.
- Existing Admin tests are updated for the new grouping.
- English and Dutch copy are present for any new labels.

## Verification Plan

- Update `frontend/src/pages/Admin.test.jsx` for section headings and restore gating.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manually verify:
  - no file selected state.
  - validation success state.
  - validation failure toast/state.
  - restore confirmation disabled/enabled state.
  - light and dark themes.

## Rollback Notes

No backend or data change is involved. Rollback restores the previous Admin layout while preserving backup/restore behavior.
