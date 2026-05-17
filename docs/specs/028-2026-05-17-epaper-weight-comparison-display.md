# 028 - E-Paper Weight Comparison Display

## Summary

Refocus the ESP32 e-paper display from a compact dashboard into a quiet weight-comparison instrument. The screen should answer only the questions that matter at a glance:

- How many litterbox visits happened today?
- What is the latest known weight?
- What was the weight about one month ago?
- What was the weight about three months ago?

The design should support one or multiple cats without becoming dense. It intentionally removes most secondary dashboard details from the 400x300 e-paper view.

## Design Direction

The display should feel like a small dedicated measurement panel, not a mini web dashboard. Use large numbers, strong spacing, and minimal decoration.

### Single Cat Layout

- Top bar:
  - cat name on the left
  - `Today` or last update time on the right
  - optional tiny status dot
- Primary row:
  - large visits-today number with label `visits today`
  - large latest weight with label `latest weight`
  - labels must have clear horizontal separation; `visits today` and `latest weight` must not visually merge
  - the visits count and latest weight value should share the same baseline
  - the latest weight column should start far enough right to read as a distinct block
- Comparison area:
  - `1 month ago` weight and delta from latest
  - `3 months ago` weight and delta from latest
- Optional tiny sparkline:
  - very small, secondary, no axes
  - removable if readability suffers

### Multi Cat Layout

For two active cats, use stacked rows/cards:

- Each cat row contains:
  - cat name
  - visits today count
  - latest weight
  - 1-month comparison
  - 3-month comparison
  - optional tiny sparkline
- Keep row heights fixed and avoid wrapping.
- If more than two cats exist, v1 may either:
  - show the two cats with visits today first, then most recently weighed
  - or paginate/alternate screens on refresh

## Visual Rules

- Target display: 400x300 landscape, black/white/red e-paper.
- Use black text on white background.
- Use red only for meaningful states:
  - warning/offline/stale status
  - large negative weight change beyond threshold
  - unknown/unidentified latest activity if shown
- Avoid full charts, axes, tables, dense timestamps, and long labels.
- Typography must remain readable on low-resolution e-paper.
- No photos, gradients, shadows, or decorative UI.

## Data Requirements

The backend display summary should expose per-cat comparison data. This can be done by extending `GET /display/summary` or adding a display-mode specific endpoint later. V1 should prefer extending the existing endpoint unless it makes the API contract awkward.

Suggested shape for each display cat:

```json
{
  "name": "Plurk",
  "visits_today": 2,
  "latest_weight_kg": 3.76,
  "latest_weight_at": "2026-05-17T15:11:00Z",
  "one_month_ago": {
    "weight_kg": 3.77,
    "measured_at": "2026-04-17T09:20:00Z",
    "delta_kg": -0.01
  },
  "three_months_ago": {
    "weight_kg": 3.91,
    "measured_at": "2026-02-17T10:40:00Z",
    "delta_kg": -0.15
  },
  "sparkline": [3.91, 3.84, 3.77, 3.76]
}
```

## Comparison Semantics

- `latest_weight_kg` uses the latest identified visit for that cat with non-null `weight_kg`.
- `one_month_ago` should find the nearest valid weight around `now - 1 month`.
- `three_months_ago` should find the nearest valid weight around `now - 3 months`.
- Use a tolerance window, for example +/- 14 days for one month and +/- 21 days for three months.
- If no comparison point exists, return `null` for that comparison and render `--` or `no data` compactly.
- Delta is `latest_weight_kg - historical_weight_kg`.
- Visits today should match the dashboard's today boundary semantics.

## Firmware Layout Behavior

- Firmware renders the display from compact JSON only; it should not do historical lookup itself.
- Refresh interval remains 5 minutes unless the endpoint says otherwise.
- If no cats have usable weight data:
  - show visits today and `No weight data yet`
- If Wi-Fi or API fetch fails:
  - keep the last rendered data if available
  - show a small red stale/offline marker
- If a cat has visits today but no weight in that visit:
  - keep showing latest known weight and do not invent a new measurement

## Relationship To Existing E-Paper Work

- Builds on spec 018, which introduced the ESP32 e-paper display view and `GET /display/summary`.
- Replaces the chart-heavy v1 layout direction with a simpler comparison-focused display.
- Keeps the 30-day chart/sparkline optional and visually secondary.
- Does not require a separate firmware project decision beyond the existing recommendation to keep firmware under `firmware/epaper-display/`.

## Acceptance Criteria

- The e-paper display shows only visits-today, latest weight, one-month comparison, and three-month comparison as primary content.
- Single-cat and two-cat layouts are both supported without overlap on 400x300.
- In the single-cat layout, the visits count and latest weight value align on the same visual row.
- In the single-cat layout, the primary labels have enough spacing to avoid reading as one joined phrase.
- Red is only used for warnings or meaningful negative deltas.
- Missing historical comparison data is handled gracefully.
- The backend provides comparison data directly; firmware does not calculate historical windows.
- Existing `/display/summary` consumers either remain compatible or are updated together with the firmware contract.

## Test Plan

### Backend

- Returns display cat comparison data for one active cat.
- Returns display cat comparison data for multiple active cats.
- Computes visits today consistently with dashboard semantics.
- Selects nearest one-month and three-month historical weights within tolerance windows.
- Returns `null` comparison values when no suitable historical weight exists.
- Computes deltas from latest minus historical weight.
- Handles inactive cats and cats without weight data safely.

### Firmware

- Parses the updated display summary JSON.
- Renders one-cat layout at 400x300 without overlap.
- Renders two-cat layout at 400x300 without overlap.
- Handles missing one-month or three-month values.
- Handles API offline/stale state with a small red marker.
- Does not render the old dense dashboard fields as primary content.

### Manual Visual QA

- Check physical e-paper readability from normal viewing distance.
- Verify the two-cat layout stays calm when both cats have visits today.
- Verify red accents remain rare and meaningful.
- Compare against the generated mockup direction from this planning session.

## Assumptions

- The operator cares more about weight trend comparison than detailed visit timing on the e-paper screen.
- One-month and three-month comparisons are more readable on e-paper than a full chart.
- The web dashboard remains the place for richer history, diagnostics, and detailed visits.
- The display is USB-powered, so a 5-minute refresh cadence remains acceptable.
