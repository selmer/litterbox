# Plan: UX Audit — Friction Points & Missing Feedback States

## Context

A design-focused audience (someone who notices UX detail) will encounter multiple friction
points in the current Litterbox UI. These range from critical interaction failures
(irreversible deletes with no confirmation) to missing feedback states (no success toasts,
no loading indicators on async actions) to navigation anti-patterns (native anchors in an
SPA). Issues are prioritized by impact on user experience, not implementation complexity.

All code references confirmed by reading the source files directly.

---

## Priority 1 — Core Interaction Failures

### 1.1 — Visits page replaces entire layout with "Loading…" on every filter/page change

**File:** `frontend/src/pages/Visits.jsx:74`

**Problem:** `setLoading(true)` is set at the top of the `fetchVisits()` effect, which
runs on every `selectedCat` or `page` change. `if (loading) return <div className="loading">Loading…</div>`
replaces the *entire page* — filter bar, table, pagination — with a plain text loader on
every interaction. The user loses all layout context, and it's unclear if their button
press registered.

**Why it matters:** This is the highest-traffic page for review/management. Clicking a
filter button makes the page go blank. Clicking Next page makes the page go blank. This
is not a "first load" experience — it's a regression on every action.

**Fix:** Split loading state into `initialLoading` (true only until first data arrives)
and a `fetching` overlay state for subsequent loads. On initial load, show the full
`Loading…` blocker. On filter/page changes, show a subtle visual on the table area (e.g.,
reduce table opacity to 0.5, show a spinner in the table header) while keeping the filter
bar and pagination in place.

```jsx
// Before: one loading state for everything
if (loading) return <div className="loading">Loading…</div>

// After: distinguish initial from subsequent fetches
const [initialLoading, setInitialLoading] = useState(true)
const [fetching, setFetching] = useState(false)

// On first fetch: setInitialLoading(false) after data arrives
// On filter/page change: setFetching(true/false) only
if (initialLoading) return <div className="loading">Loading…</div>

// Table wrapper:
<div style={{ opacity: fetching ? 0.5 : 1, transition: 'opacity 0.15s', pointerEvents: fetching ? 'none' : 'auto' }}>
  <VisitsList ... />
</div>
```

---

### 1.2 — Delete fires immediately with no confirmation or undo

**File:** `frontend/src/components/VisitsList.jsx:72-82`

**Problem:** Clicking "delete" calls `onDelete(visit)` inline, which immediately calls
`deleteVisit(visit.id)` in `Visits.jsx:49`. No confirmation dialog. No undo option.
The visit is gone. The button is red-colored (`var(--color-danger)`) which signals
danger — but gives no checkpoint before acting.

**Why it matters:** Visits are auto-generated data from the device. Accidentally deleting
one (misclick, fat-finger) means losing a real health data point permanently. A
design-focused audience has a strong expectation that destructive actions are confirmed.

**Two viable approaches:**

**Option A — Inline confirmation row (recommended):** When the user clicks "delete",
replace the row's action buttons with "Really delete?" + "Yes, delete" (red) + "Cancel".
No modal, no page disruption — the confirmation lives where the delete button was.

**Option B — Undo toast:** Immediately remove the row optimistically and show a toast:
"Visit deleted · Undo" with a 5-second window to cancel (like Gmail trash). On undo,
re-fetch the visit and re-insert. On timeout, no further action needed (already deleted).

Option A is simpler to implement. Option B feels more modern. Pick based on taste.

---

### 1.3 — No success feedback after saves

**Files:** `frontend/src/pages/Cats.jsx`, `frontend/src/pages/Dashboard.jsx`

**Problem:** After saving a cat edit, adding a cat, or adding a manual visit, the
modal/form closes silently. `useToast` is only called for *errors*, never for success.
The cat card updates inline for edits (good) but the user receives no explicit confirmation
that anything was persisted.

**Why it matters:** Silent success is a known UX anti-pattern. Users second-guess whether
it worked, especially on flaky connections. A 1-second success toast is standard
expectation.

**Fix:** Call `toast` (with a success variant) after every successful mutation. Add a
`type: 'success'` variant to the Toast component and CSS (green background instead of red).

```js
// After successful save in Cats.jsx:
toast('Changes saved', 'success')

// After adding a cat:
toast(`${name} added`, 'success')

// After saving a visit:
toast('Visit saved', 'success')
```

Toast CSS addition (index.css or App.css):
```css
.toast-success {
  background: var(--green);
  color: white;
}
/* or subtle light-green background for less intensity */
```

---

## Priority 2 — Significant Friction

### 2.1 — Reassign modal doesn't show the current assignment

**File:** `frontend/src/pages/Visits.jsx:136-180`

**Problem:** The reassign modal shows: *"Who used the litterbox at 14:32 · 4.520 kg?"*
followed by a list of cats. It doesn't say which cat the visit is *currently* assigned to.
If I'm reviewing unidentified visits, I know none are assigned — but if I'm correcting an
auto-identified visit, I'm choosing a replacement without knowing what I'm replacing.

**Fix:** Add "Currently: [Cat name]" or "Currently: unidentified" to the modal subtitle.
Mark the current cat in the list with a checkmark or visually different button state (e.g.,
`btn-primary` for the current assignment, `btn-secondary` for alternatives).

```jsx
// In the modal subtitle:
<p className="text-muted" style={{ fontSize: 13, marginBottom: 16 }}>
  Who used the litterbox at {time} · {weight}?
  {reassigning.cat_id && (
    <span> Currently assigned to <strong>{catMap[reassigning.cat_id]?.name}</strong>.</span>
  )}
</p>

// On each cat button: highlight the currently assigned one
className={`btn w-full ${cat.id === reassigning.cat_id ? 'btn-primary' : 'btn-secondary'}`}
```

---

### 2.2 — Duration input asks for raw seconds

**File:** `frontend/src/pages/Dashboard.jsx:248-260`

**Problem:** The "Add visit" form has a field labelled "Duration (seconds)" with
placeholder "e.g. 120". Users are expected to mentally convert 2 minutes and 15 seconds
into 135 seconds before typing.

**Why it matters:** This is a machine-centric interface surfaced directly to the user.
Every manual visit entry requires mental arithmetic.

**Fix:** Replace with two fields (minutes + seconds) that combine on submit, or a single
field with `mm:ss` parsing:

```jsx
// Simple two-field approach:
<div style={{ display: 'flex', gap: 8 }}>
  <input type="number" placeholder="min" min="0" step="1" style={{ flex: 1 }} />
  <input type="number" placeholder="sec" min="0" max="59" step="1" style={{ flex: 1 }} />
</div>
// On submit: duration_seconds = minutes * 60 + seconds
```

Or keep one field but label it "Duration" with placeholder "e.g. 2:15" and parse the
colon-separated format.

---

### 2.3 — Chart range buttons have no loading state

**File:** `frontend/src/components/WeightChart.jsx` (range buttons) and
`frontend/src/pages/Dashboard.jsx:81-84`

**Problem:** Clicking a range button (1W, 1M, 3M, etc.) triggers `fetchWeightHistory()`
which is a network call. The buttons have no disabled state and no loading indicator during
the fetch. On slow connections, users may click multiple times believing the first click
didn't register.

**Fix:** Pass a `loading` prop to WeightChart, disable buttons during fetch, and
optionally show a subtle spinner or "loading" text inside the chart empty state area.

```jsx
// Dashboard.jsx: track weight loading state
const [weightLoading, setWeightLoading] = useState(false)

async function handleRangeChange(newRange) {
  setDateRange(newRange)
  setWeightLoading(true)
  await fetchWeightHistory(newRange)
  setWeightLoading(false)
}

// Pass to chart:
<WeightChart weightLoading={weightLoading} ... />

// WeightChart: disable buttons during load
<button className={...} disabled={weightLoading} onClick={...}>1W</button>
```

---

### 2.4 — Pagination shows "Page X" with no total count or visit range

**File:** `frontend/src/pages/Visits.jsx:115-134`

**Problem:** Pagination reads "Page 3" — no indication of total pages or total visits.
Users don't know if they're near the end of the data or 1% through it.

**The app currently fetches `PAGE_SIZE + 1` records to detect `hasMore`, but never
fetches total count.**

**Fix (minimal — no API change):** Show record range: "Visits 101–150" calculated from
`page * PAGE_SIZE + 1` to `page * PAGE_SIZE + visits.length`. This requires no API
change and gives much better orientation.

```jsx
<span className="text-muted" style={{ fontSize: 13 }}>
  Visits {page * PAGE_SIZE + 1}–{page * PAGE_SIZE + visits.length}
</span>
```

**Fix (fuller — API change):** Add a `total` field to the visits API response and show
"Page 3 of 8" or "101–150 of 380 visits".

The minimal fix is immediately actionable.

---

## Priority 3 — Polish Gaps

### 3.1 — Native `<a href>` causes full page reload in an SPA

**File:** `frontend/src/pages/Dashboard.jsx:184, 201`

**Problem:** Two navigation links use native HTML anchors:
- `<a href="/visits">review in Visits</a>` (unidentified visits alert)
- `<a href="/visits" ...>view all →</a>` (recent visits section)

Native `<a href>` triggers a full browser navigation, discarding React state and
re-downloading the page. React Router's `<Link>` does a client-side transition.

**Fix:**
```jsx
import { Link } from 'react-router-dom'

// Replace:
<a href="/visits">review in Visits</a>
// With:
<Link to="/visits">review in Visits</Link>

// Replace:
<a href="/visits" className="text-muted" style={{ fontSize: 12 }}>view all →</a>
// With:
<Link to="/visits" className="text-muted" style={{ fontSize: 12 }}>view all →</Link>
```

---

### 3.2 — Empty state on Dashboard has no CTA button

**File:** `frontend/src/pages/Dashboard.jsx:170-177`

**Problem:** When no cats exist, the empty state reads "No cats added yet. Go to Cats to
add one." — but "Cats" is plain text, not a link or button.

**Fix:** Make the call to action actionable:
```jsx
<p>No cats added yet.</p>
<Link to="/cats" className="btn btn-primary" style={{ marginTop: 12 }}>
  Add a cat →
</Link>
```

---

### 3.3 — PollerStatus is opaque with no explanation

**File:** `frontend/src/components/PollerStatus.jsx`

**Problem:** The header shows "polling · 2 minutes ago" or "disconnected". There's no
tooltip, no explanation, and no action for the "disconnected" state. Users who don't know
what "polling" means will either ignore it or be confused. A disconnected state implies
stale data — which is directly relevant to the health monitoring purpose of the app.

**Fix:** Add a `title` attribute (tooltip) on the status element:

```jsx
// Healthy:
title="Device is connected and reporting. Last update: 2 minutes ago."

// Unhealthy:
title="Device connection lost. Data may be outdated."
```

For a richer fix, make the disconnected state visually more prominent (amber/yellow
background pill instead of just a colored dot) to signal that action may be needed.

---

### 3.4 — "Unidentified" filter is visually identical to cat name filters

**File:** `frontend/src/pages/Visits.jsx:100-105`

**Problem:** The filter bar reads "All | Griezeltje | Mitzie | Unidentified". The
Unidentified option is a semantic category (visits without an identified cat), not a cat.
It's styled and positioned identically to the cat filters, which implies it's a peer
entity.

**Fix:** Add a visual separator before "Unidentified" and/or style it differently:

```jsx
// Option A: separator element
<span style={{ color: 'var(--border)', margin: '0 4px' }}>|</span>
<button className={`btn btn-sm ${...}`}>Unidentified</button>

// Option B: different button style (e.g., dashed border or muted label prefix)
<button className={`btn btn-sm btn-ghost ${...}`}>
  ⚠️ Unidentified
</button>
```

---

## Critical Files

| File | Issues |
|------|--------|
| `frontend/src/pages/Visits.jsx` | 1.1 (loading), 2.4 (pagination), 3.4 (filter style) |
| `frontend/src/components/VisitsList.jsx` | 1.2 (delete confirmation) |
| `frontend/src/pages/Dashboard.jsx` | 1.3 (success feedback), 2.2 (duration input), 3.1 (Link), 3.2 (empty state CTA) |
| `frontend/src/pages/Cats.jsx` | 1.3 (success feedback) |
| `frontend/src/components/WeightChart.jsx` | 2.3 (chart loading state) |
| `frontend/src/components/Toast.jsx` | 1.3 (success toast variant) |
| `frontend/src/components/PollerStatus.jsx` | 3.3 (tooltip) |

---

## Verification

Each fix can be verified manually:

1. **1.1 (filter loading):** Click a cat filter on Visits — filter bar and table skeleton
   should remain visible; only the table rows should update. The layout must not go blank.

2. **1.2 (delete confirmation):** Click "delete" on any visit row — confirmation step
   should appear before data is removed. Cancelling should not delete the visit.

3. **1.3 (success toasts):** Edit a cat name and save — a green "Changes saved" toast
   should appear. Add a manual visit and save — a "Visit saved" toast should appear.

4. **2.1 (reassign context):** Open the reassign modal on an already-identified visit —
   the current cat should be shown in the subtitle and highlighted in the list.

5. **2.2 (duration input):** Open "Add visit" — duration field should accept minutes and
   seconds separately or in `mm:ss` format. No raw-seconds mental math required.

6. **2.3 (chart loading):** Click a chart range button — range buttons should be disabled
   during fetch and re-enable after. No multiple-fire on rapid clicks.

7. **2.4 (pagination range):** Navigate to page 2 — should show "Visits 51–100" (or
   similar range) instead of just "Page 2".

8. **3.1 (Link):** Click "view all →" from Dashboard — browser should not do a full page
   reload. React state (sidebar, dark mode) should be preserved across the navigation.

9. **3.2 (empty state CTA):** On an account with no cats, Dashboard empty state should
   show a clickable button, not plain text.

10. **3.3 (PollerStatus tooltip):** Hover over the poller status indicator — a tooltip
    should appear explaining what "polling" means and what "disconnected" implies.
