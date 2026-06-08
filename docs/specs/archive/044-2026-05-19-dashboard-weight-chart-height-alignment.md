# Dashboard Weight Chart Height Alignment

## Summary
The dashboard weight trend card should visually line up with the cat summary column. When two cat cards are shown on the left, the weight chart card on the right should use the same vertical space instead of leaving a large empty area below a short chart.

## Current Behavior
- The dashboard grid aligns items at the top.
- The weight chart card keeps a fixed chart height of 220px.
- With two cat cards, the right card matches neither the visual height nor the useful chart area of the left column.

## Proposed Behavior
- The desktop dashboard grid stretches both columns to the same row height.
- The weight chart card uses a column layout.
- The chart area grows to fill the available card space.
- The chart data, axis scale, tooltip, range controls, and weight history behavior remain unchanged.
- On narrow screens, the dashboard remains stacked and uses a compact chart height.

## Acceptance Criteria
- With two cat cards, the weight trend card occupies the same vertical space as the two cards together.
- The plotted chart uses the available height instead of sitting at the top with excess whitespace underneath.
- With one cat, the chart card does not receive an artificially large desktop height.
- Mobile and tablet layouts continue to stack cleanly.
- Existing WeightChart behavior and tests remain valid.

## Verification Plan
- Inspect the dashboard at desktop width with two cats.
- Inspect the dashboard at desktop width with one cat.
- Inspect the dashboard below the existing responsive breakpoint.
- Run relevant frontend checks where the local toolchain is available.
