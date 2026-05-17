# Chart and Dashboard Refinement

Priority: P2

Implementation scope:
Frontend dashboard and chart refinement. This spec improves chart readability, range persistence, dashboard empty states, and final light/dark polish after the broader UI foundation is stable.

## Summary

- Refine the dashboard without changing its core layout direction.
- Make the weight chart more readable with real data volumes.
- Improve dashboard empty/error states and final theme details.
- Keep backend dashboard and weight-history APIs unchanged.

## Key Changes

- Improve chart tick density so `1Y` and `All` ranges do not crowd the x-axis.
- Format y-axis values consistently with space-separated units, for example `3.8 kg`.
- Preserve the selected chart range in local storage.
- Keep hover tooltip concise and readable in both themes.
- Consider adding a subtle reference-weight indicator only when it is technically straightforward and visually quiet.
- Improve dashboard empty states:
  - no cats
  - cats without visits
  - no chart data for selected range
  - poller disconnected or stale
- Refine dashboard copy and action hierarchy:
  - keep `View all` as a small secondary action
  - keep Add visit contextual to a cat
  - avoid explanatory text where the UI state is already clear
- Perform a final light/dark polish pass for card borders, shadows, table tinting, chart grid lines, and muted text.

## Visual Details

- The dashboard should remain compact and operational.
- The chart is important but should not overpower the latest cat status.
- Dark mode should feel deliberate, with restrained glow and enough separation between surfaces.
- Light mode should remain crisp and professional, not washed out.

## Acceptance Criteria

- Chart labels remain readable at `1W`, `1M`, `3M`, `1Y`, and `All`.
- Selected chart range persists across reloads.
- Dashboard empty states are compact and useful.
- Poller disconnected/stale state is visible without overwhelming the dashboard.
- Recent visits, chart, and cat summary remain visually balanced in both themes.
- No backend or API changes are introduced.

## Verification Plan

- Run frontend tests for Dashboard and WeightChart behavior.
- Add or update tests for range persistence if feasible.
- Manually verify all chart ranges with sparse and dense data.
- Manually verify no cats, no visits, chart empty, poller healthy, and poller unhealthy states.
- Check desktop, tablet, and mobile widths in both themes.

## Assumptions

- Specs `020` and `021` have already provided shared primitives and icon consistency.
- This spec should not introduce new health scoring or medical interpretation.
- Backend aggregation and chart data correctness are handled by earlier backend specs.
