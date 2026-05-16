# Cat Health Monitor - Dark Elegant Design Spec

## 1. Direction

Dark Elegant is a premium, focused dark theme for the Cat Health Monitor dashboard. It should feel refined and calm, not like a gaming interface.

Reference target: the right mockup in the provided comparison image.

Design principles:

- Deep navy and slate surfaces instead of pure black.
- Soft elevation over bright borders.
- Purple accent with restraint.
- High readability for repeated monitoring.
- Pet-friendly details may remain, but the overall tone should stay grown-up and data-focused.

## 2. Typography

Primary font:

```css
font-family: "Proxima Nova", "Inter", "Segoe UI", Roboto, Arial, sans-serif;
```

Type scale:

| Element | Size | Weight | Line height | Notes |
|---|---:|---:|---:|---|
| Sidebar brand | 13px | 700 | 18px | App name beside cat icon |
| Page title | 30px | 700 | 36px | Dashboard heading |
| Date / metadata | 14px | 400 | 22px | Muted supporting text |
| Card title | 16px | 700 | 22px | Section headings |
| Cat name | 22px | 700 | 28px | Primary entity label |
| Main metric | 26px | 700 | 32px | Current weight |
| Body | 14px | 400 | 20px | Table cells and labels |
| Small label | 11px | 700 | 14px | Uppercase table headers |
| Badge text | 11px | 700 | 14px | Status badges |

Letter spacing:

- Table headers and small uppercase labels: `0.06em`.
- Body text, titles, metric text: `0`.

## 3. Color Tokens

Use these tokens from `design-tokens.json` and `theme-tokens.css`.

| Token | Value | Usage |
|---|---|---|
| `--bg-app` | `#0B1220` | Main background |
| `--bg-sidebar` | `#101827` | Sidebar |
| `--bg-card` | `#131D2E` | Cards |
| `--bg-card-elevated` | `#172236` | Raised areas |
| `--bg-subtle` | `#1D2940` | Table header, secondary panels |
| `--border-soft` | `#253247` | Card and table borders |
| `--border-strong` | `#35445E` | Focused or emphasized borders |
| `--text-primary` | `#F8FAFC` | Main text |
| `--text-secondary` | `#CBD5E1` | Secondary labels |
| `--text-muted` | `#8794A8` | Metadata, hints, axes |
| `--accent` | `#8B6CFF` | Primary accent |
| `--accent-hover` | `#9B7DFF` | Button hover |
| `--accent-soft` | `rgba(139, 108, 255, 0.16)` | Selected states |
| `--accent-border` | `rgba(139, 108, 255, 0.38)` | Accent outlines |
| `--success` | `#34D399` | Polling dot, positive delta |
| `--success-soft` | `rgba(52, 211, 153, 0.14)` | Auto badge background |
| `--chart-line` | `#8B6CFF` | Weight chart line |
| `--chart-grid` | `rgba(148, 163, 184, 0.14)` | Chart grid |

## 4. App Layout

Desktop shell:

- Sidebar width: `240px`.
- Main content max width: `1080px`.
- Main padding: `32px`.
- Vertical page gap: `24px`.
- Main background should feel continuous and quiet, with the sidebar slightly differentiated.

Recommended dashboard grid:

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(480px, 1.4fr);
  gap: 24px;
}
```

Responsive behavior:

- Below `900px`, stack summary and chart into one column.
- Below `760px`, reduce main padding to `20px`.
- Below `700px`, convert recent visits into compact dark cards.
- Ensure the sidebar or mobile navigation keeps enough contrast from the app background.

## 5. Sidebar

The sidebar should be deep, quiet, and clearly navigable.

```css
.app-sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  padding: 24px 16px;
}

.nav-item {
  height: 44px;
  border-radius: 12px;
  padding: 0 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  font-weight: 600;
}

.nav-item.active {
  color: #FFFFFF;
  background: linear-gradient(
    135deg,
    rgba(139, 108, 255, 0.34),
    rgba(139, 108, 255, 0.16)
  );
  border: 1px solid rgba(139, 108, 255, 0.28);
}
```

Avoid bright icon-only decoration. Icons should support navigation, not become the visual focus.

## 6. Header

Header layout:

- Page title in `--text-primary`.
- Date in `--text-secondary` or `--text-muted`.
- Polling status on the right in a low-contrast pill.

```css
.polling-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.polling-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--success);
}
```

## 7. Card System

Base card:

```css
.card {
  background: linear-gradient(180deg, #172236 0%, #121B2B 100%);
  border: 1px solid var(--border-soft);
  border-radius: 18px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
}
```

Card guidance:

- Do not use pure black cards.
- Do not make borders bright or neon.
- Let depth come from the difference between `--bg-app`, `--bg-card`, and the card shadow.
- Use the same radius as Light Professional for layout consistency.

## 8. Cat Summary Card

Preferred structure:

1. Top row: avatar, cat name, breed, current weight aligned right.
2. Positive delta below the weight in green.
3. Four compact metric columns with subtle dividers.
4. Footer area with the Add visit action.

Metric dividers:

```css
.summary-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}

.summary-metric {
  min-height: 76px;
  padding: 14px 12px;
  text-align: center;
  border-left: 1px solid rgba(255, 255, 255, 0.07);
}

.summary-metric:first-child {
  border-left: 0;
}
```

Add visit button:

```css
.primary-button {
  height: 36px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 10px;
  background: linear-gradient(135deg, #8B6CFF, #6F4DF5);
  color: #FFFFFF;
  font-weight: 700;
  box-shadow: 0 8px 20px rgba(139, 108, 255, 0.24);
}

.primary-button:hover {
  background: linear-gradient(135deg, #9B7DFF, #7C5CFF);
}
```

## 9. Weight Chart Card

Chart guidance:

- Line color: `var(--chart-line)`.
- Line width: `2px`.
- Optional glow: subtle, not neon.
- Grid: `var(--chart-grid)`.
- Axis labels: `var(--text-muted)`.
- Range controls should be visible but not loud.

```css
.chart-line {
  stroke: var(--chart-line);
  stroke-width: 2;
  filter: drop-shadow(0 0 8px rgba(139, 108, 255, 0.35));
}

.range-chip {
  height: 30px;
  min-width: 36px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-weight: 700;
}

.range-chip.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #FFFFFF;
}
```

## 10. Recent Visits Table

The table should remain compact and highly readable.

Table card:

- Same base card as other surfaces.
- Header row: `rgba(255, 255, 255, 0.025)`.
- Row borders: `rgba(255, 255, 255, 0.06)`.
- Alternating row tint: very subtle purple.
- Hover row: stronger purple tint, still low opacity.

```css
.recent-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.recent-table th {
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.visit-row {
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.visit-row:nth-child(even) {
  background: rgba(139, 108, 255, 0.035);
}

.visit-row:hover {
  background: rgba(139, 108, 255, 0.10);
}

.visit-cat::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 0 12px rgba(139, 108, 255, 0.50);
  display: inline-block;
  margin-right: 10px;
}

.badge-auto {
  background: var(--success-soft);
  color: var(--success);
  border: 1px solid rgba(52, 211, 153, 0.18);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 11px;
  font-weight: 700;
}
```

## 11. Interaction States

Focus:

```css
:focus-visible {
  outline: 3px solid rgba(139, 108, 255, 0.38);
  outline-offset: 2px;
}
```

Transitions:

```css
transition:
  background-color 150ms ease,
  border-color 150ms ease,
  box-shadow 150ms ease,
  transform 150ms ease;
```

Hover behavior:

- Buttons become slightly brighter.
- Table rows receive subtle purple tint.
- Cards can lift by `translateY(-1px)` if motion exists elsewhere in the app.

## 12. Accessibility Notes

- Keep all body text at least `#CBD5E1` on card surfaces.
- Do not use `--text-muted` for core values or table data.
- Ensure green text has enough contrast on `--success-soft`.
- Use focus rings on all interactive elements, including range chips and nav items.
- Avoid conveying state by color alone.

## 13. Implementation Checklist

- Apply `data-theme="dark-elegant"` at the app shell level.
- Move hard-coded dashboard colors into theme tokens.
- Add dark chart grid and axis styles.
- Verify card, table, and sidebar contrast in screenshots.
- Keep the Add visit button prominent but not neon.
- Verify mobile layout at `390px`, `768px`, and desktop width.
