# Cat Health Monitor - Future Implementation Suggestions

Priority: P2

Implementation scope:
Future frontend dashboard enhancements. This spec is a follow-up backlog and should not block the Light Professional or Dark Elegant theme implementation.

## 1. Purpose

This document captures follow-up improvements that should not block implementation of Light Professional or Dark Elegant. Treat these as a backlog of product, UX, accessibility, and engineering ideas for later rounds.

The immediate scope remains:

- Implement Light Professional as the default polished theme.
- Implement Dark Elegant as an alternate premium theme.
- Use shared tokens so both modes stay maintainable.

## 2. Recommended Implementation Order

1. Tokenize the current dashboard UI.
2. Implement Light Professional first.
3. Implement Dark Elegant using the same component structure.
4. Add a theme switch only after both themes are visually stable.
5. Add the enhancements below in small, testable slices.

## 3. Theme Architecture Suggestions

Use a single theme attribute on the app shell:

```html
<div id="root" data-theme="light-professional"></div>
```

Recommended theme values:

- `light-professional`
- `dark-elegant`

Store user preference in local storage:

```js
localStorage.setItem("cat-health-monitor-theme", themeName)
```

Fallback behavior:

- Default to Light Professional.
- Optionally respect `prefers-color-scheme: dark` later, but do not surprise users if they have manually chosen a theme.

## 4. Component Refactor Suggestions

Create or consolidate these dashboard primitives:

| Component | Purpose |
|---|---|
| `AppShell` | Sidebar, main content region, responsive shell |
| `PageHeader` | Title, date, polling status |
| `MetricCard` | Reusable metric presentation |
| `CatSummaryCard` | Current cat status and quick stats |
| `RangeSelector` | 1W, 1M, 3M, 1Y, All controls |
| `StatusBadge` | Auto/manual/status presentation |
| `RecentVisitsTable` | Desktop table and mobile card fallback |

Keep theme decisions in CSS tokens, not component props.

## 5. Data Visualization Suggestions

Weight chart improvements:

- Add a subtle normal-weight reference band when cat reference weight is known.
- Show point markers only on hover, not permanently.
- Add a tooltip with date, weight, and visit source.
- Preserve the current selected range across reloads.
- Support empty states that are calm and useful.

Potential future chart annotations:

- Sudden weight drop.
- Weight spike likely caused by sensor noise.
- First visit after long gap.
- Cleaning cycle overlay.

## 6. Health Insight Suggestions

Future dashboard cards could include:

- Weight trend over last 30 days.
- Visit frequency trend.
- Average duration trend.
- Longest gap since last visit.
- Unusual behavior alerts.

Keep insight language careful and non-diagnostic:

- Good: `Weight is lower than the recent average.`
- Avoid: `Your cat is ill.`

## 7. Recent Visits Enhancements

Useful later improvements:

- Filter by cat.
- Filter by date range.
- Filter by auto/manual identification.
- Inline correction of cat assignment.
- Expand row for raw event details.
- Export CSV for vet visits.

Mobile layout:

- Use visit cards with cat, started time, duration, weight, and badge.
- Avoid horizontal scrolling for core data.

## 8. Cat Profile Suggestions

Potential cat profile additions:

- Reference weight history.
- Photo management.
- Active/inactive status.
- Identification confidence notes.
- Manual weight correction.
- Vet note field.

Photo guidance:

- Use square crops.
- Keep cat thumbnails consistent across dashboard, table, and profile.
- Provide a fallback avatar that feels intentional, not broken.

## 9. Accessibility Suggestions

Accessibility checks to add before broader release:

- Keyboard navigation through sidebar, range chips, Add visit, and table actions.
- Visible focus rings in both themes.
- Color contrast checks for muted labels in Dark Elegant.
- Reduced motion support.
- Screen-reader labels for icon-only controls.
- Table headers correctly associated with cells.

Example:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 10. Empty, Loading, and Error States

Design these states explicitly:

| State | Recommended treatment |
|---|---|
| Loading dashboard | Skeleton rows and chart placeholder |
| No visits | Calm empty state with Add visit action |
| No weight data | Chart card explains that data will appear after visits |
| Poller offline | Header status changes from green to warning |
| API error | Inline error banner near affected surface |

Do not use large marketing-style empty states. Keep them compact and operational.

## 11. Motion Suggestions

Use motion sparingly:

- Button hover: color and small shadow shift.
- Card hover: optional `translateY(-1px)`.
- Table hover: background tint only.
- Chart range switch: quick opacity transition.

Avoid:

- Bouncy transitions.
- Long page entrance animations.
- Animated backgrounds.
- Glowing elements beyond the subtle dark chart line.

## 12. QA Checklist For Theme Implementation

Visual QA:

- Desktop screenshot for Light Professional.
- Desktop screenshot for Dark Elegant.
- Mobile screenshot at approximately `390px`.
- Tablet screenshot at approximately `768px`.
- Confirm no text overlaps.
- Confirm table data remains legible.
- Confirm chart axes and range chips are visible in both themes.

Functional QA:

- Range selector still changes data.
- Add visit action still works.
- Polling status still reflects backend state.
- Recent visits still link or navigate as expected.
- Theme preference survives reload if persistence is implemented.

Automated QA ideas:

- Component tests for theme toggle state.
- Snapshot or visual regression checks for key dashboard states.
- Accessibility tests with `axe` or equivalent.

## 13. Nice-To-Have Design Details

These are optional polish items:

- Use a small cat image thumbnail in the summary card and a tiny marker in the table.
- Add a soft border around cat photos so dark and light themes both frame them well.
- Use consistent numeric alignment for weights and durations.
- Use tabular numbers for metrics:

```css
.metric-value,
.recent-table td {
  font-variant-numeric: tabular-nums;
}
```

- Keep `View all` as a small text action, not a filled button.

## 14. Out Of Scope For The First Theme Pass

Do not include these in the initial theme implementation unless explicitly requested:

- Full redesign of routes outside Dashboard.
- New backend endpoints.
- New health scoring model.
- Chart library replacement.
- Authentication or user settings page.
- Export workflows.
- Advanced alerting.

These can be valuable later, but they will slow down the theme pass if bundled into it.
