# Frontend Dependency Audit Cleanup

Priority: P1

Problem:
`npm audit` reports frontend dependency vulnerabilities in packages used directly or transitively by the Vite/React frontend, including `axios`, `vite`, `picomatch`, `postcss`, `follow-redirects`, and `brace-expansion`.

Proposed behavior:

- Run the non-force audit remediation path first: `npm audit fix`.
- Allow package lockfile updates and compatible dependency patch/minor updates.
- Do not use `npm audit fix --force` without a separate specification, because that may introduce breaking upgrades.
- Keep frontend runtime behavior unchanged.

Acceptance criteria:

- `npm audit` reports no remaining vulnerabilities, or any remaining issue is documented with the reason it cannot be safely fixed automatically.
- `npm run lint`, `npm test`, and `npm run build` pass after dependency remediation.

Verification:

- Run `npm audit`.
- Run `npm run lint`.
- Run `npm test`.
- Run `npm run build`.
