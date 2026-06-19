# Secret History Audit - 2026-06-19

## Scope

This audit implements the non-destructive portion of spec 061. It reviewed the current tree and reachable git history for likely secret-bearing files and secret-like key names. It did not print or record secret values.

## Tooling

Initial fallback scanning used `git log`, `git ls-files`, `git grep -l`, and `rg` with value-suppressing output. Afterward, `gitleaks` v8.30.1 was downloaded to `/tmp`, checksum-verified, and used for redacted current-tree and history scans. `git-filter-repo` 2.47.0 was installed in the local `.venv` for the history rewrite.

## Findings

Current tracked files before cleanup included local Tuya/device output:

- `devices.json`
- `snapshot.json`
- `tuya-raw.json`

Current JSON key-name inspection found sensitive-looking fields in those files, including local device key, token, UUID, IP, and product key style fields. Values were intentionally not copied into this report.

Reachable git history includes sensitive candidate files:

- `tinytuya.json`
- `tuya-raw.json`
- `devices.json`
- `snapshot.json`

History keyword scanning also found expected configuration/example/code references such as API key, API secret, password, token, and authorization terms. Many of those matches are expected placeholders or variable names, but the historical presence of `tinytuya.json` and local Tuya output means credentials/device data should be treated as plausibly exposed.

## Actions Taken

The safe current-tree cleanup from spec 058 was performed:

- Removed local Tuya/device output from git tracking while leaving local copies on disk:
  - `devices.json`
  - `snapshot.json`
  - `tuya-raw.json`
- Removed tracked generated/starter artifacts:
  - `alembic/versions/__pycache__/2342687751a4_initial_schema.cpython-314.pyc`
  - `frontend/public/vite.svg`
  - `frontend/src/assets/react.svg`
  - root `package-lock.json`
- Updated `.gitignore` and `.dockerignore` to keep those artifacts out of future commits and Docker build context.

## Decision

A local history rewrite was performed after creating a backup bundle at `/tmp/litterbox-pre-history-rewrite-2026-06-19.bundle`.

The rewrite removed these paths from reachable history:

- `tinytuya.json`
- `tuya-raw.json`
- `devices.json`
- `snapshot.json`

The rewrite also replaced the secret values detected by `gitleaks` with `***REMOVED_SECRET***` using `git-filter-repo --replace-text`. Secret values were not copied into this report.

Post-rewrite verification showed:

- `gitleaks detect --source . --redact`: no leaks found.
- History filename scan for the removed Tuya JSON paths: no matches.
- Current-tree `gitleaks` scan: no leaks found.

## Required Follow-Up

Rotate any Tuya credentials and local device keys that were present in historical `tinytuya.json`, `tuya-raw.json`, `devices.json`, or `snapshot.json` data. History rewrite does not revoke already exposed credentials and cannot clean old clones, caches, forks, or backups.

Force-push the rewritten history to the remote only after confirming credential rotation and making sure any other clones are ready to re-clone or hard-reset.

## Suggested Next Commands

Useful verification commands after rewrite:

```bash
gitleaks detect --source . --redact
git log --all --name-only --pretty=format: | sort -u | rg '(tinytuya\.json$|tuya-raw\.json$|devices\.json$|snapshot\.json$)'
```

Before force-pushing, prepare a short checklist covering credential rotation, branch/tag handling, fresh-clone verification, and deployment clone recovery.
