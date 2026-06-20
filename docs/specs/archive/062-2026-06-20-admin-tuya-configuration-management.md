# 062 - Admin Tuya Configuration Management

Priority: P1

Implemented: 2026-06-20

## Summary

Add Admin-managed Tuya configuration backed by a generic `app_settings` table. Secrets may be stored in the database, are only exposed as configured/missing state in the UI, are excluded from backup exports, and can be applied without a container restart through poller reload.

## Scope

- Add `app_settings` with `key`, `value`, `is_secret`, and timezone-aware `updated_at`.
- Resolve Tuya settings from DB first and environment second.
- Seed missing Tuya settings from existing environment values on startup.
- Add Admin API endpoints for get, update, test, and reload.
- Add an Admin UI operations card for Tuya configuration.
- Exclude secret `app_settings` rows from backup and restore only non-secret settings.

## Acceptance Criteria

- `/admin/tuya-config` never returns API key or API secret plaintext.
- Blank secret fields on save preserve the existing secret.
- New secret values replace existing values.
- Test connection uses saved or draft config without persisting drafts.
- Save/reload can reinitialize the active poller client without restarting the container.
- Backup metadata notes that app settings secrets are excluded.
- Backup database export contains non-secret settings and omits secret values.

## Verification

- `.venv/bin/python -m pytest`
- `PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run lint`
- `PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm test -- --run`
- `PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run build`
- `PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm audit --json`
