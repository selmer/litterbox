# Local npm Global Config Warning Cleanup

Priority: P2

Problem:
Every npm command emits `npm warn Unknown global config "tmp"` because the local global npm configuration contains the removed `tmp` option. The warning is not caused by repository code or frontend dependencies, but it makes verification output noisy.

Proposed behavior:

- Remove only the unsupported `tmp` entry from the npm global configuration when that config is writable.
- If the global npm config is read-only, provide a repo-local clean npm global config and use it from repository validation/deploy commands through `NPM_CONFIG_GLOBALCONFIG`.
- Do not change project dependencies, npm scripts, or repository runtime behavior.
- Leave other npm config values unchanged.

Acceptance criteria:

- Repository npm validation commands no longer report `Unknown global config "tmp"`.
- Frontend verification commands remain green.

Verification:

- Run `NPM_CONFIG_GLOBALCONFIG=frontend/.npm-globalconfig npm config list`.
- Run `npm run lint`.
