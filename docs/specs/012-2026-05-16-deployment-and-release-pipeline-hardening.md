# Deployment and Release Pipeline Hardening

Priority: P1

Problem:
`deploy.sh` pulls, installs dependencies, runs backend tests, builds frontend, commits local tracked changes, pushes, and SSH deploys in one script (`deploy.sh:10-49`). It does not run frontend tests or lint, uses hard-coded NAS details, runs `npm install` rather than `npm ci`, and changes `node_modules` ownership with sudo.

Current behavior:

- Deployment mutates local git state and may commit unrelated tracked changes.
- Frontend quality gates are omitted from deploy.
- Environment assumptions are embedded in the script.
- Local missing tools break verification, as seen in this assessment environment.

Proposed behavior:

- Split validation, packaging, and deployment into separate commands.
- Use reproducible installs: `pip` in a virtual environment or container, and `npm ci`.
- Add frontend lint/test/build gates.
- Move NAS host/path/user to environment variables or a deploy config excluded from git.
- Prefer CI or a containerized validation command that matches production.

Acceptance criteria:

- A validation command can run without committing or deploying.
- Deployment refuses to proceed with dirty unrelated changes unless explicitly allowed.
- Frontend lint and tests are required before deployment.
- NAS details are configurable without editing the script.

Verification:

- Add a dry-run validation mode.
- Run backend tests, frontend lint, frontend tests, and frontend build in the release workflow.
- Confirm deploy works from a clean checkout.
