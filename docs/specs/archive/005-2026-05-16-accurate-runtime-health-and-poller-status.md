# Accurate Runtime Health and Poller Status

Priority: P0

Problem:
The polling loop updates `last_successful_poll_at` immediately after every `poller.poll()` call in `app/main.py:40-42`, even when `poll()` returns after cloud initialization failure, cloud read failure, unexpected responses, or empty DPs in `app/poller.py:93-114`.

Current behavior:

- Polling mode can look healthy while device reads are failing.
- `/health` only returns process liveness in `app/main.py:87-89`.

Proposed behavior:

- Track explicit poll outcomes: success, skipped, failed, last error, and last attempted timestamp.
- Update `last_successful_poll_at` only when cloud device state is processed successfully.
- Add health response fields or a separate status endpoint for device update health.

Acceptance criteria:

- Failed cloud responses do not refresh the dashboard's successful poll timestamp.
- Dashboard status distinguishes process health from device update health.
- Tests cover successful polling, failed polling, and stale polling cases.

Verification:

- Add backend tests for `LitterboxPoller.poll()` outcome reporting.
- Add dashboard tests for polling health states.
- Manually simulate failed Tuya responses and confirm dashboard health turns unhealthy.
