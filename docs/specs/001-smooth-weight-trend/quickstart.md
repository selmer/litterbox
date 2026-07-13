# Quickstart: Smooth Weight Trend

## Prerequisites

- Repository dependencies are available.
- For frontend commands, use the local Node path from `docs/AGENTS.md` if `npm` is not already on `PATH`:

```bash
cd frontend
PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run lint
```

## Focused Validation

1. Run the chart tests:

```bash
cd frontend
PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm test -- --run src/components/WeightChart.test.jsx
```

Expected outcome:

- Noisy same-cat sample data produces fewer plotted direction reversals than the raw measurements.
- Tooltip/context data still includes the original recorded weight and visit id.
- One-point and two-point cat histories are not smoothed.
- Multiple cats remain independent series.

2. Run frontend lint:

```bash
cd frontend
PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm run lint
```

Expected outcome:

- ESLint exits successfully with no unused variables or style violations.

3. Run npm audit:

```bash
cd frontend
PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm audit
```

Expected outcome:

- Audit result is reviewed and reported. Any vulnerability findings are inspected before choosing a fix.

## Broader Frontend Regression Check

Run the frontend test suite when time allows:

```bash
cd frontend
PATH=/home/selmer/.nvm/versions/node/v24.15.0/bin:$PATH npm test
```

Expected outcome:

- Existing dashboard, visits, cats, diagnostics, and chart tests continue to pass.

## Manual Review Scenario

1. Start the app in the normal local development mode.
2. Open the dashboard.
3. Use a data set with one cat that has at least 10 recent weights alternating slightly around a stable value.
4. Confirm the visible trend is smoother than the raw point-to-point sequence.
5. Confirm recorded measurements and visit ids remain available in chart context.
6. Switch date ranges and confirm smoothing remains scoped to the selected range.
