# Cat Health Monitor - Light Professional Design Spec

## 1. Direction

Light Professional is the recommended default theme for day-to-day use. It should feel calm, precise, modern, and trustworthy: clinical enough for health data, warm enough for pet care.

Reference target: the middle mockup in the provided comparison image.

Design principles:

- Quiet information density over decorative composition.
- White and near-white surfaces with crisp but soft borders.
- Purple as the product accent, used sparingly and consistently.
- Green only for healthy, active, positive, or confirmed states.
- Rounded but professional UI: no playful oversized pills, no marketing-style hero treatment.

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
| `--bg-app` | `#F7F8FB` | Main app background |
| `--bg-sidebar` | `#FFFFFF` | Sidebar background |
| `--bg-card` | `#FFFFFF` | Cards, table surfaces |
| `--bg-subtle` | `#F4F1FF` | Active nav, active filters, soft panel fills |
| `--border-soft` | `#E7EAF0` | Card and table borders |
| `--border-strong` | `#D7DCE6` | Focused or emphasized borders |
| `--text-primary` | `#111827` | Main text |
| `--text-secondary` | `#4B5563` | Secondary labels |
| `--text-muted` | `#8A94A6` | Metadata, hints, axes |
| `--accent` | `#7C5CFF` | Primary accent |
| `--accent-hover` | `#6847F5` | Button hover |
| `--accent-soft` | `#EEE9FF` | Selected states |
| `--accent-border` | `#D9CEFF` | Accent outlines |
| `--success` | `#22C55E` | Polling dot, positive delta |
| `--success-soft` | `#DCFCE7` | Auto badge background |
| `--chart-line` | `#7C5CFF` | Weight chart line |

## 4. App Layout

Desktop shell:

- Sidebar width: `240px`.
- Main content max width: `1080px`.
- Main padding: `32px`.
- Vertical page gap: `24px`.
- Content should align left inside the main area; do not center narrow cards in a way that makes the dashboard feel sparse.

Recommended dashboard grid:

```css
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(480px, 1.4fr);
  gap: 24px;
}

.recent-visits {
  margin-top: 24px;
}
```

Responsive behavior:

- Below `900px`, stack summary and chart into one column.
- Below `760px`, use a compact top header and reduce main padding to `20px`.
- Below `700px`, convert recent visits from table rows into compact visit cards.
- Sidebar may become icon-only, drawer, or bottom navigation depending on the existing app pattern.

## 5. Sidebar

The sidebar should be simple and stable, with the active page clearly indicated without heavy decoration.

```css
.app-sidebar {
  width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-soft);
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
  color: var(--accent);
  background: var(--accent-soft);
}
```

Navigation icons:

- Dashboard: layout/grid icon.
- Visits: calendar or clipboard icon.
- Cats: cat, tag, or hexagon-style identity icon.

Use one icon per item. Avoid adding secondary badges unless there is meaningful state.

## 6. Header

Header layout:

- Page title and date on the left.
- Polling status on the right.
- The date should be visibly secondary, not a competing title.

Polling indicator:

```css
.polling-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 30px;
  padding: 0 12px;
  border: 1px solid var(--border-soft);
  border-radius: 999px;
  background: #FFFFFF;
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

Use copy like `Polling` and `3 minutes ago`; do not add extra explanatory text in the UI.

## 7. Card System

Base card:

```css
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-soft);
  border-radius: 18px;
  box-shadow: 0 12px 30px rgba(17, 24, 39, 0.06);
}
```

Card padding:

- Default: `24px`.
- Dense table card: `18px 20px`.
- Compact footer bands: `16px`.

Avoid cards inside cards. If a card needs a footer or secondary band, make it a subtle section within the same card rather than a floating nested panel.

## 8. Cat Summary Card

Preferred structure:

1. Top row: avatar, cat name, breed, current weight aligned right.
2. Positive delta below the weight in green.
3. Four compact metric columns: visits today, time in box, last visit, duration.
4. Soft footer containing the Add visit action.

Avatar:

- Size: `64px`.
- Border radius: `12px`.
- Object fit: cover.

Metric row:

```css
.summary-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--border-soft);
  border-bottom: 1px solid var(--border-soft);
}

.summary-metric {
  min-height: 76px;
  padding: 14px 12px;
  text-align: center;
  border-left: 1px solid var(--border-soft);
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
  border: 1px solid var(--accent-border);
  border-radius: 10px;
  background: var(--accent);
  color: #FFFFFF;
  font-weight: 700;
}

.primary-button:hover {
  background: var(--accent-hover);
}
```

## 9. Weight Chart Card

The chart is the largest analytical surface and should remain clean and legible.

Chart guidance:

- Line color: `var(--chart-line)`.
- Line width: `2px`.
- Fill: none, or at most a 4% accent tint.
- Grid: dashed `#E6EAF2`.
- Axis labels: `var(--text-muted)`.
- Avoid chart shadows or glow in the light theme.
- Keep range controls in the top-right of the chart header.

Range chips:

```css
.range-chip {
  height: 30px;
  min-width: 36px;
  border: 1px solid var(--border-soft);
  border-radius: 9px;
  background: #FFFFFF;
  color: var(--text-secondary);
  font-weight: 700;
}

.range-chip.active {
  background: var(--accent-soft);
  border-color: var(--accent-border);
  color: var(--accent);
}
```

## 10. Recent Visits Table

The table should be readable first, colorful second.

Table card:

- White card surface.
- Same radius and border as other cards.
- Header row with `#FAFBFD`.
- Rows height: `52px`.
- Row border: `1px solid #EEF1F5`.
- Hover: pale lavender.

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

.visit-row:nth-child(even) {
  background: #FBFAFF;
}

.visit-row:hover {
  background: #F6F2FF;
}

.visit-cat::before {
  content: "";
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--accent);
  display: inline-block;
  margin-right: 10px;
}

.badge-auto {
  background: var(--success-soft);
  color: #16A34A;
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
  outline: 3px solid rgba(124, 92, 255, 0.28);
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

- Buttons darken slightly.
- Table rows get a subtle lavender tint.
- Cards may lift by `translateY(-1px)` only if the app already uses motion.

## 12. Implementation Checklist

- Apply `data-theme="light-professional"` at the app shell level.
- Move hard-coded dashboard colors into theme tokens.
- Use the compact summary card layout from the reference image.
- Replace plain table rows with the accented row system above.
- Verify text contrast for all muted labels.
- Verify mobile layout at `390px`, `768px`, and desktop width.
- Keep the `auto` badge green and the range selection purple.
