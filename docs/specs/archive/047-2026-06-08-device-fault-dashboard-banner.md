# Device Fault Dashboard Banner

## Summary
Show active litterbox device faults as a compact persistent red banner on the dashboard. The banner appears only when Tuya `fault` reports a non-zero value. Device settings such as deodorization remain out of scope.

## Current Behavior
- The poller receives raw Tuya DP state but does not expose `fault` through `/dashboard`.
- The dashboard shows poller connectivity and unidentified visits, but not active device fault codes.

## Proposed Behavior
- Decode Tuya `fault` bitmap values into stable labels: `motor_fault`, `program_fault`, and `g_sensor_fault`.
- Preserve unknown fault bits as fallback labels such as `unknown_fault_code_8`.
- Add `device_faults` and `device_fault_code` to `/dashboard`.
- Show a red dashboard alert below the page header when device faults are active.
- Keep the existing poller-offline alert; if both are active, show poller first and device fault second.

## Acceptance Criteria
- `fault = 0` returns no faults and no banner.
- Known single and combined bitmap values return readable labels.
- Unknown bitmap values return fallback labels.
- Dashboard banner links to `/diagnostics`.
- English and Dutch translations exist for known faults and banner copy.

## Verification Plan
- Backend dashboard tests for zero, known, combined, and unknown fault values.
- Frontend dashboard tests for no banner, single fault, multiple faults, diagnostics link, and poller + fault coexistence.
- Run `.venv/bin/python -m pytest tests/test_api_dashboard.py`.
- Run `cd frontend && npm run lint` and `cd frontend && npm test` where Node is available.
