# 036 - Trusted Duration and Adaptive Visit Polling

## Summary
Keep visit duration in the product, but stop showing fake certainty. Legacy 30-minute timeout durations should be treated as unknown, and future automatic durations should only be trusted when they come from a real Tuya completion signal or manual correction. Add tightly budgeted adaptive polling while a visit is open to improve the chance of catching Tuya's short-lived completion status without permanently increasing API usage.

## Problem
Duration has been unreliable in live use. Report-log reconciliation often returns no logs, and 5-minute polling can miss short visits where Tuya only exposes `excretion_time_day` briefly. The current safe behavior closes unresolved visits with `duration_source=hard_timeout` and `duration_seconds=null`, but older fallback visits may still show as 30-minute durations when their source is `unknown`.

## Key Changes
- Treat duration as trusted only when `duration_source` is one of:
  - `status_dp`
  - `report_log_counter`
  - `report_log_duration`
  - `manual`
- Treat these durations as unknown in API/dashboard/display/frontend output:
  - `duration_source=hard_timeout`
  - `duration_is_estimated=true`
  - legacy fallback visits with `duration_source=unknown` and `duration_seconds >= 1800`
- Add a data cleanup migration or runtime-safe backfill for legacy fallback visits:
  - set `duration_source=hard_timeout`, `duration_is_estimated=true`, and `duration_seconds=null` for likely timeout-only 30-minute records
  - preserve manually created or trusted-source durations
- Add adaptive polling behind environment flags:
  - `ADAPTIVE_VISIT_POLLING=false` by default, or conservatively enabled only after validation
  - `ADAPTIVE_POLL_INTERVAL_SECONDS=30`
  - `ADAPTIVE_POLL_MAX_SECONDS=600`
  - `ADAPTIVE_POLL_DAILY_BUDGET=200`
  - `ADAPTIVE_POLL_COOLDOWN_SECONDS=3600` after Tuya rate-limit or repeated errors
- When a weight starts an open visit, temporarily poll Tuya status faster until one of these happens:
  - completion status is captured and visit closes with trusted duration
  - max adaptive window expires
  - daily adaptive budget is exhausted
  - Tuya returns an error or rate-limit response
- Keep report-log reconciliation as fallback/diagnostics, but do not depend on it as the primary duration source.
- Add diagnostics for adaptive polling:
  - `adaptive_poll_started`
  - `adaptive_poll_attempt`
  - `adaptive_poll_budget_exhausted`
  - `adaptive_poll_stopped`
  - include request counts, elapsed seconds, reason, and relevant DPS values.

## Public Interfaces
- Existing visit API shape remains unchanged.
- Duration fields keep current semantics:
  - `duration_seconds` is `null` when unknown/untrusted.
  - `duration_source` explains why.
  - `duration_is_estimated` flags unresolved fallback closure.
- New optional environment variables configure adaptive polling.
- `GET /visits/{id}/diagnostics` shows adaptive polling diagnostics when used.

## Implementation Notes
- Do not increase normal idle polling frequency.
- Adaptive polling should call the same status path used by normal polling and reuse existing `_handle_changes` behavior where possible.
- Persist daily adaptive request counters in process memory first; if restarts make this too loose, add a small runtime-state table later.
- If adaptive polling catches `excretion_times_day` without a valid positive `excretion_time_day`, close only when a real duration can be derived; otherwise keep unknown rather than inventing a duration.
- Existing hard-timeout behavior remains: close unresolved visits without a trusted duration.

## Test Plan
- Backend unit tests:
  - legacy `duration_source=unknown`, `duration_seconds=1800` is hidden from `VisitOut`.
  - dashboard totals ignore legacy fallback 30-minute durations.
  - display summary ignores legacy fallback 30-minute durations.
  - trusted durations from `status_dp`, `report_log_counter`, `report_log_duration`, and `manual` still show.
  - hard-timeout visits remain hidden as unknown.
- Poller tests:
  - adaptive polling starts only after an open visit begins.
  - adaptive polling stops after completion, max window, budget exhaustion, or Tuya error.
  - adaptive polling captures a short-lived status completion and closes with `duration_source=status_dp`.
  - adaptive request count never exceeds configured per-visit and daily limits.
  - diagnostics are recorded for start/attempt/stop/budget/error paths.
- Frontend tests:
  - visits and dashboard show `-`/unknown for untrusted fallback durations.
  - trusted durations still render normally.

## Assumptions
- Tuya API usage should stay conservative; adaptive polling must be bounded and configurable.
- It is better to show unknown than an inaccurate 30-minute duration.
- Manual correction remains the fallback when Tuya never exposes a trustworthy completion duration.
- If adaptive polling still fails to capture completions in real use, auto-duration should remain best-effort and low-prominence rather than removed entirely.
