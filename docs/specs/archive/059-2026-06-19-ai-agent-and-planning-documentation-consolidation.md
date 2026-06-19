# AI Agent and Planning Documentation Consolidation

Priority: P2

Implementation scope:
Repository documentation, GitHub automation, active planning files, and agent handoff conventions. This spec removes Claude-specific workflow/docs now that Codex is the only AI agent expected to work on the project.

## Summary

- Remove Claude-specific GitHub workflows and documentation.
- Consolidate agent instructions into a root bootstrap plus one canonical repo guidance document.
- Remove or archive old AI planning folders that are not part of the current spec-driven workflow.
- Update README documentation links so contributors know where current planning and agent guidance live.

## Problem

The repository still contains Claude-specific workflows and planning artifacts even though project operation now assumes Codex is the only AI agent. Multiple agent instruction surfaces create ambiguity about which rules apply, and old planning folders make it harder to distinguish active specs from historical notes. The root `AGENTS.md` should remain as a small bootstrap so agents reliably discover `docs/AGENTS.md`.

Observed examples:

- `.github/workflows/claude.yml`
- `.github/workflows/claude-code-review.yml`
- `docs/CLAUDE.md`
- `docs/AGENTS.md`
- `MEMORY/WORK/20260324-143000_frontend-performance-audit/PRD.md`
- `Plans/nifty-hopping-fountain.md`
- `Plans/stateless-fluttering-liskov.md`

## Current Behavior

- GitHub Actions can still invoke Claude workflows when matching events occur and required secrets exist.
- `docs/CLAUDE.md` contains Claude-specific instructions.
- `docs/AGENTS.md` exists separately, creating two possible agent guidance entry points.
- The README describes the spec workflow under `docs/specs/`, but old `MEMORY/` and `Plans/` folders remain outside that canonical process.

## Proposed Behavior

Canonicalize agent guidance:

- Keep `AGENTS.md` as a short root bootstrap pointing to `docs/AGENTS.md`.
- Keep `docs/AGENTS.md` as the authoritative project guidance document.
- Rewrite it to describe the current Codex-oriented collaboration rules at a repository level:
  - spec-first workflow for non-trivial changes.
  - respect for user changes and dirty worktrees.
  - expected validation commands.
  - cleanup policy for generated/local files.
  - documentation update expectations.

Remove Claude-specific files:

- `.github/workflows/claude.yml`
- `.github/workflows/claude-code-review.yml`
- `docs/CLAUDE.md`

Handle old planning folders:

- Remove `MEMORY/` and `Plans/` if their contents are obsolete and duplicated by `docs/specs/`.
- If any content is still valuable, migrate the useful parts into either:
  - a new numbered spec under `docs/specs/`, or
  - an archived note under `docs/archive/`.

Update README:

- Mention `AGENTS.md` as the root bootstrap and `docs/AGENTS.md` as the authoritative project guidance file.
- Keep `docs/specs/` as the only active planning/spec location.
- Remove any references to deprecated agent/planning locations.

## Implementation Notes

- Check all files for references to `CLAUDE.md`, Claude workflows, `MEMORY/`, and `Plans/` before deletion.
- If `.github/workflows/` becomes empty after removing Claude workflows, remove the empty directory from git implicitly.
- Do not introduce new automation unless explicitly requested.
- Keep the documentation concise; this is a cleanup, not a new process framework.
- If `docs/AGENTS.md` already contains useful non-Claude content, preserve it and edit in place.

## Non-Goals

- Do not add a Codex GitHub Action or remote AI automation.
- Do not change application behavior.
- Do not rewrite historical implementation specs.
- Do not delete current active specs.
- Do not remove ordinary project documentation such as `docs/SPECIFICATION.md`, `docs/update-modes.md`, or `docs/backup-restore.md`.

## Acceptance Criteria

- No tracked Claude workflow files remain.
- No tracked `docs/CLAUDE.md` remains.
- `AGENTS.md` is a short bootstrap and `docs/AGENTS.md` is the authoritative agent guidance document.
- `MEMORY/` and `Plans/` are removed or their still-useful content is migrated to the canonical docs/spec structure.
- README points contributors to `AGENTS.md`, `docs/AGENTS.md`, and `docs/specs/`.
- Repository search for `CLAUDE`, `Claude Code`, `MEMORY/`, and `Plans/` returns no active-process references outside historical archived notes, if any.

## Verification Plan

- Run:

```bash
rg -n 'CLAUDE|Claude Code|MEMORY/|Plans/' . -g '!frontend/node_modules/**' -g '!frontend/dist/**' -g '!firmware/epaper-display/.pio/**'
```

- Confirm any remaining matches are intentionally historical or removed.
- Run:

```bash
git ls-files '.github/workflows/*' docs/CLAUDE.md AGENTS.md docs/AGENTS.md MEMORY Plans
```

- Confirm only the intended canonical documentation remains.
- Run documentation link checks manually by opening README references.
- Run backend/frontend tests only if implementation touches commands, config, or behavior. Pure documentation/workflow deletion does not require the full test suite, but `./deploy.sh validate` may be run as a confidence check.

## Rollback Notes

Rollback is a normal git revert. If Claude automation is intentionally restored later, it should be reintroduced as a conscious workflow decision with updated secrets, permissions, and README documentation rather than by restoring stale files silently.
