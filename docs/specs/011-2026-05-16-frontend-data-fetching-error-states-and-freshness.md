# Frontend Data Fetching, Error States, and Freshness

Priority: P1

Problem:
Dashboard initial loading fetches dashboard, weight history, recent visits, and cats in `frontend/src/pages/Dashboard.jsx:55-73`, but the 15-second refresh updates only the dashboard summary in `frontend/src/pages/Dashboard.jsx:79-83`. The Visits page suppresses dependency linting for its fetch effect in `frontend/src/pages/Visits.jsx:23-46` and does not expose retry or persistent error UI.

Current behavior:

- Dashboard cards refresh but recent visits, cats, and charts can become stale.
- API failures often collapse to generic messages or console logs.
- Some fetch paths lack cancellation or stale-response protection.

Proposed behavior:

- Centralize API error handling and normalize user-visible error messages.
- Refresh dashboard-adjacent data according to clear freshness rules.
- Add request cancellation or stale-response guards for page/filter changes.
- Replace the Visits fetch dependency suppression with stable callbacks or a small data-fetch helper.

Acceptance criteria:

- Recent visits update after an automatic device visit without full page reload.
- Failed API requests show actionable retry affordances.
- Rapid filter changes on Visits cannot display stale results from older requests.
- Lint can run without disabling hook dependency checks for data fetching.

Verification:

- Add frontend tests for dashboard refresh, Visits filter race handling, and error retry states.
- Run `npm run lint` and `npm test`.
