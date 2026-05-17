# 033 - E-Paper Display Profiles

## Summary

Add configurable e-paper display profiles so the operator can change what the ESP32 screen shows without reflashing firmware for every product/layout preference.

## Problem

The desired e-paper display evolved quickly: dashboard summary, chart, then weight comparison, then removing static header text. Firmware-only layout changes make iteration slow. Display profiles let the backend choose a mode and the firmware render a known small set of layouts.

## Proposed Profiles

Initial profiles:

- `weight_comparison`
  - current spec 028 layout
- `today_only`
  - visits today and latest weight only
- `alerts_only`
  - mostly blank unless a meaningful signal/alert exists
- `multi_cat_rotation`
  - rotates active cats across refreshes if more than two cats exist

## Backend Scope

- Add a display settings source, initially config/env or simple persisted setting.
- Include profile in `GET /display/summary`:

```json
{
  "display_profile": "weight_comparison"
}
```

- Shape data so firmware can render known profiles without extra fetches.
- Keep `refresh_after_seconds` profile-aware.

## Firmware Scope

- Route rendering by `display_profile`.
- Keep unknown profile fallback to `weight_comparison`.
- Avoid dynamic layout engines; implement a small fixed set of known layouts.
- Keep 400x300 readability as the main constraint.

## UI Scope

- Add display profile setting later, likely under Settings or Diagnostics.
- Show a small preview/description of each mode.
- Do not require firmware upload for changing profiles once supported.

## Acceptance Criteria

- Backend includes selected display profile in display summary.
- Firmware renders at least `weight_comparison` through profile dispatch.
- Unknown profiles fall back safely.
- Refresh interval can vary by profile.
- No firmware reflash is needed to switch between supported profiles once settings UI/API exists.

## Test Plan

- Backend tests for default profile and configured profile.
- Firmware parse/render tests for known and unknown profiles.
- Manual e-paper checks for each profile.
- Regression check that existing spec 028 layout remains unchanged under `weight_comparison`.
