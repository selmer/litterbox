# Plan: File Size and Loading Performance Audit

## Context

A performance audit of the Litterbox frontend and backend identified five high-impact
issues affecting initial page load time. The current setup serves a 653 KB uncompressed
JS bundle with no cache headers, loads Google Fonts via a blocking CSS `@import`, has no
code splitting, and no vendor chunk separation. These five changes address the biggest
gains in order of impact.

---

## Changes (ranked by impact)

### 1 — Add GZip compression middleware (`app/main.py`)

**Problem:** FastAPI serves the 653 KB JS bundle and all assets uncompressed. Over any
network, this is the single largest avoidable cost on first load.

**Fix:** Add `GZipMiddleware` from Starlette (already a FastAPI dependency — no new
packages):

```python
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

Add after the CORS middleware (line 72). `minimum_size=1000` skips tiny responses where
compression overhead isn't worth it.

**Estimated gain:** 653 KB JS → ~175 KB over the wire (~73% reduction).

---

### 2 — Long-lived cache headers for hashed Vite assets (`app/main.py`)

**Problem:** Vite outputs content-hashed filenames (e.g. `index-DVlr_pcc.js`). The hash
changes whenever code changes, so these files are safe to cache forever — but the current
`StaticFiles` mount sends no `Cache-Control` header. Every page visit re-downloads
identical assets.

**Fix:** Replace the bare `StaticFiles` mount for `/assets` with a custom route that
injects immutable cache headers:

```python
from fastapi.responses import FileResponse as _FR
from fastapi import Request

@app.get("/assets/{path:path}")
async def serve_assets(path: str):
    file = FRONTEND_DIST / "assets" / path
    response = _FR(file)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response
```

Remove the existing `app.mount("/assets", ...)` line (line 97).

**Estimated gain:** Repeat visitors load from disk cache; zero network bytes for JS/CSS.

---

### 3 — Move Google Fonts from CSS `@import` to HTML `<link>` with preconnect
(`frontend/src/index.css` and `frontend/index.html`)

**Problem:** `index.css` line 1 uses `@import url('https://fonts.googleapis.com/...')`.
CSS `@import` is render-blocking: the browser must finish downloading and parsing the
stylesheet before it discovers the font request, creating a waterfall delay.

**Fix — two parts:**

**Part A** — Remove the `@import` from `frontend/src/index.css` line 1.

**Part B** — Add `<link>` tags in `frontend/index.html` `<head>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500&family=DM+Mono:wght@400;500&display=swap"
/>
```

`preconnect` hints warm the DNS + TLS connection before the browser parses HTML, so the
font CSS download starts as early as possible.

**Estimated gain:** Fonts begin loading in parallel with the rest of the page instead of
sequentially after CSS parse; removes ~200–300 ms from LCP on cold connections.

---

### 4 — Vite manual chunks to split recharts from app code (`frontend/vite.config.js`)

**Problem:** The entire 653 KB bundle is one file: app code, recharts, react, react-dom,
axios, and date-fns are all merged. When app code changes on deploy, the browser must
re-download and re-parse the full bundle — including the static recharts library — even
though recharts didn't change.

**Fix:** Add `build.rollupOptions` to split the bundle into stable vendor chunks:

```js
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-charts': ['recharts'],
          'vendor-utils': ['axios', 'date-fns'],
        },
      },
    },
  },
  test: { ... },  // unchanged
})
```

**Estimated gain:** App-only chunk is much smaller (~80–120 KB); recharts chunk (~200 KB)
is separately cached and survives app deploys. Better long-term cache utilisation.

---

### 5 — Route-level code splitting with `React.lazy` (`frontend/src/App.jsx`)

**Problem:** `App.jsx` lines 3–5 import all three page components statically. The browser
downloads and parses JS for Dashboard, Visits, and Cats on every initial load, regardless
of which page the user opens.

**Fix:** Replace static imports with `React.lazy` and wrap `<Routes>` in `<Suspense>`:

```jsx
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Visits    = lazy(() => import('./pages/Visits'))
const Cats      = lazy(() => import('./pages/Cats'))

// inside AppShell render:
<Suspense fallback={<div className="main-content" style={{ padding: '2rem' }}>Loading…</div>}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/visits" element={<Visits />} />
    <Route path="/cats" element={<Cats />} />
  </Routes>
</Suspense>
```

With manual chunks in place (change #4), each page's unique imports will land in its own
chunk and only download when that route is visited.

**Estimated gain:** Initial parse work limited to the current page; Visits and Cats pages
(including their imports) load on demand.

---

## Critical Files

| File | Change |
|------|--------|
| `app/main.py` | Add GZipMiddleware (after CORS, line 72); replace `/assets` mount with caching route (line 97) |
| `frontend/index.html` | Add preconnect + stylesheet `<link>` tags in `<head>` |
| `frontend/src/index.css` | Remove `@import` line 1 |
| `frontend/vite.config.js` | Add `build.rollupOptions.output.manualChunks` |
| `frontend/src/App.jsx` | Replace static imports with `React.lazy`; add `<Suspense>` wrapper |

---

## Verification

1. **GZip** — `curl -I -H "Accept-Encoding: gzip" http://localhost:8000/assets/index-*.js`
   → response should include `Content-Encoding: gzip`.
2. **Cache headers** — same `curl -I` → response should include
   `Cache-Control: public, max-age=31536000, immutable`.
3. **Google Fonts** — open browser DevTools Network tab on first load; fonts request should
   appear as a `<link>` resource in the initial waterfall, not as a sub-request inside the
   CSS waterfall.
4. **Chunk splitting** — `npm run build` in `frontend/` → `dist/assets/` should contain
   multiple JS files (vendor-react-*.js, vendor-charts-*.js, etc.) instead of one large
   index-*.js.
5. **Lazy routes** — navigate to `/visits` directly; DevTools Network tab should show a
   new JS chunk loading at that moment, not on initial page load.
6. Run `npm run test` in `frontend/` — all existing tests should still pass.
