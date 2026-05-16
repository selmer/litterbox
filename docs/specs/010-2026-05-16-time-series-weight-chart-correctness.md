# Time-Series Weight Chart Correctness

Priority: P1

Problem:
The weight chart groups points by `format(timestamp, 'dd MMM')` in `frontend/src/components/WeightChart.jsx:43-58`, which loses the year, overwrites multiple same-day points for a cat, and sorts with `new Date(a.date)` on incomplete date strings.

Current behavior:

- Multi-year ranges can merge different years into the same date key.
- Multiple visits on the same day overwrite earlier values for the same cat.
- Sorting depends on JavaScript parsing of partial localized date strings.

Proposed behavior:

- Use stable timestamp keys, such as ISO date or full timestamp depending on desired granularity.
- Preserve multiple points per day or explicitly aggregate by day with a documented rule.
- Sort by numeric timestamp.
- Format labels only at render time.

Acceptance criteria:

- A one-year and all-time chart preserves year boundaries.
- Multiple same-day visits do not silently disappear unless an aggregation rule says so.
- Chart ordering is stable across browsers and locales.
- Tooltip labels display human-readable dates while data keys remain machine-stable.

Verification:

- Add frontend tests for cross-year data, same-day multiple visits, and ordering.
- Manually inspect chart behavior with synthetic multi-year data.
