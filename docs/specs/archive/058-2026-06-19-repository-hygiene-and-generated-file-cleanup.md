# Repository Hygiene and Generated File Cleanup

Priority: P1

Implementation scope:
Git tracking hygiene, generated files, local device artifacts, ignore rules, and validation. This spec removes files that should not be source-controlled while preserving database migrations, examples, and runtime documentation.

## Summary

- Remove generated Python bytecode, cache directories, build output, and tool artifacts from source control.
- Stop tracking local Tuya/device output files that are already intended to be ignored.
- Keep Alembic migration source files, examples, and operational docs.
- Tighten `.gitignore` and `.dockerignore` so the same clutter does not return.

## Problem

The repository currently mixes source files with generated and local-machine artifacts. This makes reviews noisier, increases the chance of leaking device-specific data, and obscures the true codebase shape.

Observed examples:

- `alembic/versions/__pycache__/2342687751a4_initial_schema.cpython-314.pyc` is tracked.
- Runtime/generated files such as `devices.json`, `snapshot.json`, and `tuya-raw.json` are tracked even though related ignore rules exist.
- Local build/cache folders exist in the worktree, including `.pytest_cache/`, `__pycache__/`, `frontend/dist/`, `frontend/node_modules/`, and `firmware/epaper-display/.pio/`.
- `bfg.jar` is present at the repository root and should remain local-only.
- Root `package-lock.json` exists without a matching root `package.json` and contains no useful dependency graph.

## Current Behavior

- `.gitignore` already ignores common Python caches, virtualenvs, build output, local databases, BFG jars, and Tinytuya output files.
- Some files matching those categories are already tracked, so ignore rules no longer affect them.
- `.dockerignore` ignores broad categories such as `.venv`, `__pycache__`, tests, git metadata, Markdown docs, frontend build output, and frontend dependencies.
- Alembic migration source files under `alembic/versions/*.py` are tracked and required.

## Proposed Behavior

Remove from source control:

- All tracked Python bytecode and cache artifacts:
  - `*.pyc`
  - `__pycache__/`
  - `.pytest_cache/`
- Local dependency/build artifacts:
  - `frontend/node_modules/`
  - `frontend/dist/`
  - `firmware/epaper-display/.pio/`
  - `.venv/`
- Local tooling artifacts:
  - `bfg.jar`
- Local Tuya/device output:
  - `devices.json`
  - `snapshot.json`
  - `tuya-raw.json`
- Empty/unnecessary root package metadata:
  - `package-lock.json`, unless a real root `package.json` is introduced in the same change.

Keep in source control:

- `alembic/versions/*.py`
- `tinytuya.json.example`
- `.env.example`
- `tools/.env.example`
- `firmware/epaper-display/include/config.example.h`
- `frontend/package-lock.json`
- All backend and frontend tests.

Update ignore rules so they clearly cover:

- Python cache files at any depth.
- Local Tuya generated files.
- Uploaded user content, while preserving placeholder/example files if any are later added.
- Frontend and firmware build output.
- Local tool binaries such as `*.jar`.

## Implementation Notes

- Use `git rm --cached` for files that should remain locally but no longer be tracked.
- Use normal deletion for tracked artifacts that are safe to remove from the worktree, such as bytecode and starter/build output.
- Do not remove `alembic/versions/`; only remove generated files inside it.
- Before removing `devices.json`, `snapshot.json`, or `tuya-raw.json`, confirm no application code or tests require them.
- If any test needs representative Tuya data, replace the dependency with a small fixture under `tests/fixtures/` with anonymized data.
- Keep the cleanup commit limited to repository hygiene; avoid behavior changes.

## Non-Goals

- Do not rewrite git history to purge previously committed secrets or artifacts.
- Do not change runtime Tuya polling behavior.
- Do not alter database schemas or Alembic migration history.
- Do not reorganize application modules.
- Do not remove tests.
- Do not change deployment behavior except for ignore-file improvements.

## Acceptance Criteria

- No tracked `*.pyc` files remain.
- No tracked `__pycache__/` or `.pytest_cache/` paths remain.
- `devices.json`, `snapshot.json`, and `tuya-raw.json` are no longer tracked unless a documented source-code dependency proves one must stay.
- `bfg.jar` is not tracked.
- Root `package-lock.json` is removed unless paired with a real root JavaScript package.
- `alembic/versions/*.py` migration files remain tracked.
- `frontend/package-lock.json` remains tracked.
- `.gitignore` prevents the removed generated/local artifacts from reappearing.
- `git status --ignored` shows local generated artifacts as ignored rather than untracked.

## Verification Plan

- Run `git ls-files | rg '(__pycache__|\.pyc$|\.pytest_cache)'` and confirm no matches.
- Run `git ls-files devices.json snapshot.json tuya-raw.json bfg.jar package-lock.json` and confirm only intentionally retained files appear.
- Run `rg -n 'devices\.json|snapshot\.json|tuya-raw\.json' app tests tools docs README.md` and confirm there is no required runtime/test dependency on removed files.
- Run backend tests:

```bash
python3 -m pytest
```

- Run frontend checks:

```bash
cd frontend
npm run lint
npm test
npm run build
```

- Run deployment validation if available in the local environment:

```bash
./deploy.sh validate
```

## Rollback Notes

Rollback is a normal git revert for source-control changes. Local generated files may still exist on developer machines because `.gitignore` does not delete files. If removed Tuya sample data is later needed for tests, reintroduce it as anonymized fixtures under `tests/fixtures/` rather than restoring local runtime output at the repository root.
