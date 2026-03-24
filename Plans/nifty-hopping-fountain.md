# Plan: Fix Firefox photo display bug

## Context

Uploaded cat photos don't show in Firefox. Two independent causes were found — one
Firefox-specific, one a general caching edge case that's more visible in Firefox.

---

## Root Causes

### 1. Canvas JPEG encoding without white background fill (Firefox-specific)

**File:** `frontend/src/components/CatPhotoUpload.jsx`, `cropAndCompress()` (line 33–38)

```js
const canvas = document.createElement('canvas')
canvas.width = width
canvas.height = height
canvas.getContext('2d').drawImage(img, ...)     // ← no background fill
return canvas.toDataURL('image/jpeg', 0.85)     // ← JPEG has no alpha channel
```

JPEG has no transparency support. When a PNG with an alpha channel is drawn onto a canvas
and then exported to JPEG:
- **Chrome**: silently composites transparent pixels over white → valid JPEG
- **Firefox**: composites over black (or produces corrupted data in some versions) → the
  browser receives a broken JPEG and refuses to display it

This affects the preview in the modal AND the saved file on the server, since the corrupted
bytes are what get uploaded and stored.

### 2. Stale browser cache on re-upload (cache invalidation miss)

**File:** `frontend/src/components/CatCard.jsx`, `handleSavePhoto()` (line 41)

```js
const updated = await uploadCatPhoto(catIdValue, dataUrl)
setPhoto(updated.photo_url || null)   // → "/uploads/cat_photos/1.jpg"
```

After upload the server returns the same URL as before
(`/uploads/cat_photos/{id}.jpg`). When `photo` state already holds that URL, React
doesn't change the DOM `src` attribute and the browser serves the previously cached image.
Firefox's HTTP cache is more conservative about re-fetching than Chrome's, making this
more noticeable there.

---

## Files to Modify

| File | Change |
|------|--------|
| `frontend/src/components/CatPhotoUpload.jsx` | Fill white background in `cropAndCompress` before drawing image |
| `frontend/src/components/CatCard.jsx` | Append `?v=<timestamp>` to photo URL after every upload/delete |

---

## Implementation

### Fix 1 — `CatPhotoUpload.jsx`: white background before JPEG export

In `cropAndCompress`, after creating the canvas, fill white before drawing:

```js
function cropAndCompress(img, srcX, srcY, srcW, srcH) {
  // ... existing dimension calculation unchanged ...
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = '#ffffff'            // ← ADD: white background
  ctx.fillRect(0, 0, width, height)    // ← ADD
  ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, width, height)
  return canvas.toDataURL('image/jpeg', 0.85)
}
```

Two lines added. Nothing else changes.

### Fix 2 — `CatCard.jsx`: cache-busting on upload/delete

In `handleSavePhoto`, append `?v=<timestamp>` so the browser treats the URL as fresh:

```js
const updated = await uploadCatPhoto(catIdValue, dataUrl)
const url = updated.photo_url ? `${updated.photo_url}?v=${Date.now()}` : null
setPhoto(url)
onPhotoChange?.(updated)
```

And the same for the delete branch:
```js
const updated = await deleteCatPhoto(catIdValue)
setPhoto(updated.photo_url ? `${updated.photo_url}?v=${Date.now()}` : null)
```

The `?v=` param is only in component state — it's never persisted. On next page load
`photo_url` comes from the API without the param, which is fine since by then the
cache for the clean URL has been refreshed.

---

## Critical Files

- `frontend/src/components/CatPhotoUpload.jsx` — `cropAndCompress()` lines 21–38
- `frontend/src/components/CatCard.jsx` — `handleSavePhoto()` lines 26–48

---

## Verification

1. Upload a PNG with a transparent background in Firefox → preview and saved photo should
   show with white background (not black) and load correctly on the dashboard.
2. Upload a second photo for the same cat in Firefox → the new photo should appear
   immediately (not the old cached one).
3. Same steps in Chrome — both should still work as before.
4. No backend changes, no test changes needed — this is frontend-only.
