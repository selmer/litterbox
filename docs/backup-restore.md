# Backup and Restore

Backups are zip archives created by `GET /admin/backup`.

## Archive layout

- `metadata.json`: backup metadata, including `format_version`, `app`, `created_at`, and `schema_revision`.
- `database.json`: JSON export of every SQLAlchemy-managed application table.
- `uploads/`: uploaded application files, currently cat photos.

The archive intentionally does not include secrets, environment files, Tuya credentials, Docker volumes, or Postgres internals.

## Restore flow

1. Send a base64-encoded archive to `POST /admin/restore/validate`.
2. Review the returned metadata, table counts, and upload count.
3. Send the same archive to `POST /admin/restore` with `confirm: true`.

Restore replaces the current application database rows and uploaded files with the contents of the archive. Archive paths are validated before use and absolute paths, `..` segments, and unexpected top-level entries are rejected.
