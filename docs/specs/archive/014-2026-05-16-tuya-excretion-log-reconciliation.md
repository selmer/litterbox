# Tuya Excretion Log Reconciliation

Priority: P0

Problem:
The app reads the correct Tuya duration DP, `excretion_time_day`, but 5-minute polling reads only the latest device status. Short visit-completion events can be missed between polls, so active visits often close through the fallback timeout even though the Tuya app shows an excretion time.

Current behavior:

- Visit start is triggered by nonzero `cat_weight`.
- Visit completion is triggered only when the latest status poll observes `excretion_times_day` changing.
- If completion is not observed, `_check_visit_timeout()` closes the visit after `VISIT_TIMEOUT_SECONDS` and stores the timeout duration.

Proposed behavior:

- Keep 5-minute status polling unchanged for Tuya API quota safety.
- Before closing an overdue active visit by timeout, query Tuya status report logs for `excretion_times_day`, `excretion_time_day`, and `cat_weight`.
- Look back from the visit start time with a small buffer through the current timeout check time.
- If report logs show `excretion_times_day` advanced after the visit started, close the visit using the matching or latest `excretion_time_day` value.
- Keep visits open after the 5-minute soft timeout when report logs are unavailable, empty, or do not show completion, so later polls can retry reconciliation.
- Use a hard timeout after 30 minutes as the fallback for truly stuck visits.
- Prefer `excretion_times_day` counter completion, but allow a positive `excretion_time_day` duration log around the active visit when the counter signal is missing or unusable.
- Log whether a visit closed by latest-status completion, report-log counter reconciliation, report-log duration reconciliation, pending retry, or hard timeout.

Acceptance criteria:

- Existing status-poll completion behavior remains unchanged.
- Overdue visits can close with Tuya's reported excretion duration instead of timeout duration.
- Report-log lookup failures keep the visit open until a later retry or the hard timeout.
- Report logs without a completion counter can still close a visit when a valid positive duration log is present in the active visit window.
- Invalid, zero, negative, or out-of-window duration logs do not close a visit.

Verification:

- Run `python3 -m pytest tests/test_poller.py -q`.
- Run `python3 -m pytest tests/ -q`.
- Run `rg -n "excretion_time_day|report-logs|timeout" docs app tests`.
