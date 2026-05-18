# Durable Poller State and Restart Recovery

Priority: P0

Problem:
Active visit and cleaning-cycle state is held in memory through `current_visit_id`, `current_cleaning_cycle_id`, and `last_weight_at` in `app/poller.py:62-67`. If the process restarts during a visit or cleaning cycle, the app can lose in-progress state and fail to close records correctly.

Current behavior:

- Visit start, weight updates, visit completion, timeout, and cleaning cycle state are tracked by a single process-local poller instance.
- There is no startup recovery for open `Visit` or `CleaningCycle` rows.
- `last_weight_at` is not persisted, so timeout behavior cannot survive restart.

Proposed behavior:

- Persist enough in-progress state to recover after restart.
- On startup, rehydrate open visits and open cleaning cycles from the database.
- Store last weight timestamp, latest raw weight, and device event counters when needed for deterministic recovery.
- Define duplicate and out-of-order DP handling for restart windows.

Acceptance criteria:

- A visit started before restart can be completed or timed out after restart.
- A cleaning cycle started before restart can be ended after restart.
- Startup recovery is deterministic when multiple open records exist.
- Recovery logs enough context for operators to understand what happened.

Verification:

- Add tests that create open records, instantiate a fresh poller, and process completion events.
- Add tests for timeout after restart.
- Run migration tests if a new state table or columns are added.
