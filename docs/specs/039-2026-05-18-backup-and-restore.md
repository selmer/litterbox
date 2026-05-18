# 039 - Backup and Restore

## Summary
Add an admin-facing backup and restore workflow for the application data. A backup should contain the database contents plus uploaded files such as cat photos, so a NAS install can be recovered or migrated without hand-editing database volumes.

## Key Changes
- Add an Admin or Settings UI section for backup/restore.
- Create a backup artifact that contains:
  - database export
  - `uploads/` contents
  - metadata such as creation timestamp, schema revision, and app/version information when available
- Add restore flow with archive upload, validation, explicit confirmation, and clear success/error states.
- Exclude secrets and environment configuration from backups.
- Validate archive paths to prevent path traversal during restore.

## Public Interfaces
- Add backend endpoints for creating a backup, validating a restore artifact, and performing restore after confirmation.
- Add frontend controls for downloading a backup and uploading/restoring one.
- Backup format should be documented enough to debug manually if needed.

## Test Plan
- Backup includes database data and uploaded cat photos.
- Restore recreates cats, visits, events, diagnostics, settings/history, and uploads in a test database.
- Invalid, malformed, incompatible, or path-traversal archives are rejected safely.
- UI shows loading, confirmation, success, and error states.

## Assumptions
- Backup/restore v1 uses an Admin UI.
- Backup includes database plus uploads.
- Secrets, `.env`, Tuya credentials, and unrelated Docker/Postgres internals are out of scope.
