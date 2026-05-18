# Frontend Lint Gate Cleanup

Priority: P1

Problem:
Frontend lint blocks deployment because toast code exports a hook from the same module as components, several tests use Vitest globals without importing them, and a few imports are unused.

Proposed behavior:

- Keep `Toast.jsx` component-only for React Fast Refresh.
- Move the toast context hook to a small shared module and update existing imports.
- Import Vitest globals explicitly in tests that use them.
- Remove unused imports.

Acceptance criteria:

- `npm run lint` passes for the affected frontend files.
- Toast runtime behavior and tests remain unchanged.

Verification:

- Run `npm run lint`.
