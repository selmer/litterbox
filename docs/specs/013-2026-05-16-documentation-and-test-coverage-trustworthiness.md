# Documentation and Test Coverage Trustworthiness

Priority: P2

Problem:
Documentation and test inventories need to stay synchronized with the repository so contributors can trust the verification instructions.

Current behavior:

- Test documentation can drift from the actual test inventory without an explicit checklist.
- Some important behaviors lack tests: photo upload hardening, visit API edge cases, deployment workflow, and frontend chart correctness.
- New contributors may run the wrong verification set.
- Push/webhook/pub-sub work is intentionally deferred to a future dedicated specification.

Proposed behavior:

- Maintain a generated or manually verified test inventory in docs.
- Add missing tests for visit API, photo upload, chart behavior, and health semantics.
- Add a lightweight docs verification checklist to future specs.
- Update `docs/SPECIFICATION.md` whenever public behavior changes.

Acceptance criteria:

- README and specification list only tests that exist.
- Each implemented improvement includes matching test additions or an explicit no-test rationale.
- New specs include documentation-update requirements.
- The repository has one authoritative verification command list.

Verification:

- Run `rg --files tests frontend/src | rg 'test'` and compare with docs.
- Run backend and frontend test suites in an environment with required tools.
- Review docs in the same PR as behavior changes.
