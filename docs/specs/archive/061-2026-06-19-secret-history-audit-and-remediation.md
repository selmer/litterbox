# Secret History Audit and Remediation

Priority: P1

Implementation scope:
Repository secret scanning, credential rotation, git history assessment, optional history rewrite, and contributor/deployment coordination. This spec covers security remediation for secrets or sensitive device artifacts that may have been committed now or in the past.

## Summary

- Audit the current tree and full git history for secrets and sensitive device data.
- Rotate any credentials that may have been exposed before attempting history cleanup.
- Decide explicitly whether git history rewrite is required.
- If rewriting history, coordinate force-push, clone reset instructions, cache cleanup, and deployment follow-up.
- Keep this separate from ordinary repository hygiene cleanup.

## Problem

Repository cleanup can remove sensitive files from the current source tree, but that does not remove them from existing commits. Files such as local Tuya outputs, device snapshots, environment files, or accidental config dumps may contain credentials, device IDs, local network details, API keys, tokens, or other household-specific data.

If sensitive values were committed, simply deleting the files in a later commit is insufficient. Anyone with access to the repository history may still be able to recover them. Conversely, rewriting history is disruptive and should not be performed casually as part of a normal cleanup PR.

Potentially sensitive tracked or historical paths include:

- `tuya-raw.json`
- `devices.json`
- `snapshot.json`
- `.env` variants, if ever committed
- `tinytuya.json`, if ever committed
- firmware config files such as `firmware/epaper-display/include/config.h`, if ever committed
- deployment files or scripts containing real hosts, passwords, tokens, or API secrets

## Current Behavior

- `.gitignore` ignores common environment and Tinytuya generated files.
- Some generated/local Tuya files are currently tracked or have been tracked.
- `bfg.jar` is present locally, suggesting history cleanup tooling may have been considered or used before.
- There is no documented secret scanning or credential rotation procedure for this repository.
- Existing cleanup spec 058 intentionally treats history rewrite as a non-goal.

## Proposed Behavior

Perform remediation in this order:

1. Inventory likely sensitive files and values.
2. Scan the current tree and full git history for secrets.
3. Rotate credentials that are confirmed exposed or plausibly exposed.
4. Decide whether history rewrite is necessary.
5. If required, rewrite history with an approved tool and coordinated rollout.
6. Document the result and add prevention checks where practical.

Recommended scanning targets:

- Current working tree.
- All reachable git history.
- Tags and branches.
- GitHub Actions workflows and deployment scripts.
- Example config files, ensuring examples contain fake values only.

Recommended tools, subject to local availability:

- `gitleaks`
- `trufflehog`
- `git filter-repo`
- BFG Repo-Cleaner

Credential rotation should happen before or alongside history cleanup because removed history does not guarantee that old clones, forks, logs, caches, or backups are clean.

## Implementation Notes

- Treat findings as sensitive. Do not paste real secrets into issues, specs, commits, or chat logs.
- Prefer reporting secret types and file paths, not secret values.
- If a real secret is found, rotate it even if history rewrite is planned.
- If only non-secret local data is found, document why history rewrite is not needed.
- If history rewrite is required, create a short operator checklist before force-pushing.
- Notify any users or systems with existing clones that they must re-clone or hard-reset after history rewrite.
- Check whether deployment targets, NAS paths, CI caches, package artifacts, or backups contain old repository copies.
- Keep anonymized fixtures under `tests/fixtures/` if tests need representative payloads.

## Non-Goals

- Do not combine this work with routine generated-file cleanup from spec 058.
- Do not perform a history rewrite without explicit approval immediately before the destructive step.
- Do not publish secret values in documentation or commit messages.
- Do not remove legitimate migration history or source files unless they contain sensitive values and replacement is planned.
- Do not assume deletion from GitHub removes secrets from all clones, forks, caches, or backups.

## Acceptance Criteria

- Current tree and full git history have been scanned with at least one credible secret scanning tool.
- Findings are summarized by type, affected path, and remediation status without exposing secret values.
- Any exposed or plausibly exposed credentials are rotated or explicitly documented as no longer valid.
- A decision is recorded: history rewrite required or not required.
- If history rewrite is required:
  - affected paths/patterns are listed.
  - tool and command plan are documented before execution.
  - force-push and clone recovery instructions are prepared.
  - tags/branches are handled intentionally.
- If history rewrite is not required, the rationale is documented.
- `.gitignore` and examples prevent recurrence for known sensitive file types.
- No tests or app behavior depend on real sensitive local data.

## Verification Plan

- Run a current-tree scan, for example:

```bash
gitleaks detect --no-git --source .
```

- Run a history scan, for example:

```bash
gitleaks detect --source .
```

- Optionally run a second scanner for confidence:

```bash
trufflehog git file://. --only-verified
```

- Search for known sensitive filenames in tracked history:

```bash
git log --all --name-only --pretty=format: | sort -u | rg '(\.env$|tinytuya\.json|tuya-raw\.json|devices\.json|snapshot\.json|config\.h$)'
```

- Confirm current tracked files exclude local secret/device artifacts after spec 058 is implemented:

```bash
git ls-files | rg '(\.env$|tinytuya\.json|tuya-raw\.json|devices\.json|snapshot\.json|config\.h$)'
```

- If history rewrite is performed, rerun the scanners on a fresh clone after force-push.
- Verify app tests after any fixture replacement:

```bash
python3 -m pytest
cd frontend
npm run lint
npm test
npm run build
```

## Rollback Notes

Credential rotation cannot be rolled back safely; old exposed credentials should remain revoked. A history rewrite can be difficult to reverse once force-pushed and consumed by collaborators or deployment systems. Before rewriting history, create a protected backup reference or mirror in a restricted location, document the exact command plan, and get explicit operator approval.
