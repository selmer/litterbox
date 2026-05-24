# Android Weight Chart Rendering

Priority: P1

Implementation scope:
Frontend dashboard weight chart rendering on mobile browsers. This spec fixes the weight-over-time chart not displaying on Android Chrome and Firefox while preserving existing chart data behavior, range controls, and desktop layout intent.

## Summary

The dashboard weight-over-time graph can fail to display on Android Chrome and Firefox even though it displays on desktop Fedora browsers. The likely cause is the Recharts `ResponsiveContainer` being configured with `height="100%"` while its parent chart body has only `min-height` and flex sizing, not a definite resolved height in all mobile layout paths.

The fix should make the chart container height explicit enough for Recharts to measure reliably on Android, without changing the backend weight-history API or the chart's data transformation logic.

## Current Behavior

- The `WeightChart` renders a Recharts `ResponsiveContainer` with `width="100%"` and `height="100%"`.
- The immediate chart body uses flex growth and `min-height: 220px`.
- The dashboard grid stretches on desktop but switches to a single-column stacked layout below the responsive breakpoint.
- On Android Chrome and Firefox, the chart can appear blank instead of drawing the line, axes, and grid.
- The empty state is not shown when data exists, so the failure presents as a rendering/layout problem rather than a no-data state.

## Suspected Root Cause

- Percentage heights require an ancestor with a definite computed height.
- `min-height` does not always give Recharts a measurable parent height when `ResponsiveContainer` observes layout on Android.
- The mobile grid and flex layout can leave the chart body with a valid visual minimum size in CSS but a `ResizeObserver` measurement that Recharts treats as zero or invalid.
- Desktop browsers may resolve this layout generously enough that the problem is hidden.

## Proposed Behavior

- The chart body should expose a stable, definite height for the Recharts container at mobile, tablet, and desktop widths.
- The chart should continue to grow visually in desktop layouts where the dashboard card is intentionally stretched to match the cat summary column.
- The stacked mobile layout should use a compact but explicit chart height.
- The fix should not alter:
  - weight-history API requests
  - date range persistence
  - tooltip content
  - cat series colors
  - chart data grouping and sorting
  - empty-state behavior for genuinely empty weight data

## Implementation Notes

- Prefer a CSS-only fix if it can make Recharts measurements reliable across layouts.
- Candidate approach:
  - give `.weight-chart-card__body` a definite `height` or `flex-basis`, while keeping an appropriate `min-height`
  - keep desktop stretch behavior by allowing the body to grow when the card itself is stretched
  - add a mobile-specific height if needed below the existing responsive breakpoint
- Alternative approach:
  - pass a numeric height to `ResponsiveContainer` or use an `aspect`-based configuration
  - only choose this if CSS sizing remains unreliable or conflicts with the desktop height-alignment behavior
- Avoid introducing a new charting library or rewriting the chart component.

## Acceptance Criteria

- On Android Chrome, the weight-over-time chart renders whenever `weightHistory` contains at least one data point.
- On Android Firefox, the weight-over-time chart renders whenever `weightHistory` contains at least one data point.
- On desktop Chrome/Firefox on Fedora, the chart continues to render as before.
- The mobile stacked dashboard layout remains clean, with the chart visible and not collapsed.
- The desktop dashboard still respects the existing chart height-alignment intent from spec `044`.
- The no-data empty state still appears only when `chartData.length === 0`.
- Existing `WeightChart` tests continue to pass.

## Verification Plan

- Run the frontend test suite or the focused `WeightChart` tests.
- Inspect the dashboard in a desktop browser at a wide viewport.
- Inspect the dashboard below the existing `980px` breakpoint.
- Inspect the dashboard around a phone-sized viewport such as `390px` wide.
- Confirm the chart body has a non-zero measured height in browser devtools.
- Verify on a real Android device or Android remote debugging if available:
  - Chrome
  - Firefox
- If a real Android device is not available, use responsive browser emulation as a partial check and mark real-device verification as remaining risk.

## Non-Goals

- Changing the backend `/visits/weight-history` endpoint.
- Changing weight filtering, confidence handling, or date-range semantics.
- Adding new chart features or annotations.
- Reworking the dashboard layout beyond the minimum chart sizing fix.

## Residual Risk

- If Android rendering still fails after the container has a definite height, the next suspects are Recharts `ResizeObserver` timing or SVG/CSS variable rendering. In that case, add a small chart remount or resize-trigger workaround only after confirming the measured chart body height is non-zero.
