# Semantic Color and Theme Balance

Priority: P2

Implementation scope:
Frontend theme tokens, chart colors, badges, alerts, and high-frequency accent usage. This spec keeps the existing visual identity while reducing accent overuse and improving semantic color clarity.

## Summary

- Keep the current light-professional and dark-elegant themes.
- Reduce overuse of the purple accent in non-primary surfaces.
- Make semantic states more visually distinct and consistent.
- Improve chart color differentiation for multiple cats.

## Problem

The current theme is cohesive, but the accent color appears in many unrelated roles:

- primary buttons
- active navigation
- chart line
- subtle backgrounds
- active filters
- avatar placeholders
- card highlights
- badges

When one accent carries identity, selection, chart data, and decorative emphasis, the UI can feel visually flattened. It also makes semantic states compete with brand color.

## Current Behavior

- `frontend/src/index.css` defines purple accent tokens and applies them widely.
- `frontend/src/components/WeightChart.jsx` uses `var(--chart-line)` as the first cat color, which maps to the accent.
- Active nav items, active filter chips, chart line, and many subtle surfaces all use accent variants.
- Semantic states exist for green, yellow, and red, but accent is still the dominant visual signal.

## Proposed Behavior

Introduce clearer color roles:

- Brand/accent:
  - primary action
  - active navigation
  - selected controls
- Data visualization:
  - chart series palette distinct from primary action where practical.
  - multiple cat colors should remain distinguishable in light and dark themes.
- Semantic status:
  - success, warning, danger, muted, and info states should use semantic tokens.
- Decorative/subtle surfaces:
  - use neutral background tokens more often.
  - reserve accent-soft for selection or identity moments.

The UI should still feel like the same product after the change, just calmer and easier to parse.

## Implementation Notes

- Add or refine tokens in `frontend/src/index.css`, such as:
  - `--info`
  - `--info-soft`
  - `--data-1` through `--data-6`
  - `--selection-bg`
  - `--selection-border`
- Update `WeightChart.jsx` to use data-series tokens instead of hardcoded/accent-heavy colors.
- Review these classes for accent overuse:
  - `.sidebar-logo-mark`
  - `.nav-item.active`
  - `.filter-chip.active`
  - `.chart-range-btn.active`
  - `.cat-avatar-icon`
  - `.health-signal--info`
  - `.badge-accent`
  - `.diagnostics-row-highlight`
- Keep warning and danger states visually stronger than accent when actual attention is required.
- Do not introduce gradients or decorative blobs.

## Non-Goals

- Do not redesign layout.
- Do not remove dark mode.
- Do not introduce a new brand identity.
- Do not change content or workflows.
- Do not add external design dependencies.

## Acceptance Criteria

- Primary action and active navigation still feel clearly branded.
- Chart series colors are distinct from primary actions and distinguishable from each other.
- Warning, danger, success, muted, and info states use semantic tokens consistently.
- The UI no longer uses accent-soft for most subtle/decorative backgrounds.
- Light and dark themes both pass a visual smoke check for contrast and state clarity.
- No text becomes harder to read in either theme.

## Verification Plan

- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manually review:
  - Dashboard with health signals and device faults.
  - Weight chart with at least two cats.
  - Visits filters and badges.
  - Cats active/inactive badges.
  - Admin backup/restore states.
  - Diagnostics highlights.
- Check light and dark themes at desktop and mobile widths.

## Rollback Notes

No data or API change is involved. Rollback restores the previous theme token values and component color references.
