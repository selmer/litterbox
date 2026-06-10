# 031 - Cat Health Signals

## Summary

Add simple, non-diagnostic health signals based on each cat's own recent baseline: weight trend, visit frequency changes, and unidentified activity. The feature should surface gentle prompts, not medical conclusions.

## Problem

The app collects useful longitudinal data, but the operator still has to inspect charts manually. A lightweight signal layer can highlight meaningful changes without pretending to diagnose illness.

## Proposed Signals

- Weight trend:
  - notable decrease over 1 month or 3 months
  - notable increase over 1 month or 3 months
- Visit frequency:
  - fewer visits than recent baseline
  - more visits than recent baseline
- Data quality:
  - repeated unidentified visits
  - stale poller/device data

## Product Language

Avoid medical claims. Use phrasing like:

- `Weight is down compared with 3 months ago.`
- `Visits are lower than usual this week.`
- `Several visits could not be assigned to a cat.`

Do not say:

- `Plurk is sick.`
- `This indicates kidney disease.`

## Backend Scope

- Add a signal computation helper or endpoint, likely included in dashboard output.
- Compute per-cat baselines using recent visit/weight history.
- Include severity levels:
  - `info`
  - `watch`
  - `attention`
- Include enough metadata for UI explanation: comparison window, baseline, current value.

## UI Scope

- Dashboard shows a compact signal area when signals exist.
- Cat profile/card can show the most relevant signal.
- Empty/no-signal state should be quiet; do not celebrate absence of alerts loudly.
- E-paper may later show only severe/stale signals in red.

## Acceptance Criteria

- Signals are per-cat and based on that cat's own data.
- Signals are explainable from visible values.
- No medical diagnosis language is used.
- Missing/sparse data results in no signal or an `insufficient data` explanation.
- Signals do not overwhelm the dashboard when everything is normal.

## Test Plan

- Backend tests for weight decrease/increase signals.
- Backend tests for visit frequency deviations.
- Backend tests for insufficient data.
- Frontend tests for signal rendering and empty state.
- Copy review to ensure language remains non-diagnostic.


## Implementation Notes

Built with live computation in `app/health_signals.py`; no migration or persisted signal table was added. The dashboard response now includes a sorted `health_signals` list and each cat summary includes its most relevant `health_signal`.

Threshold choices:

- Weight: latest non-ignored weight is compared with the nearest measurement around 1 month ago, tolerance 14 days, and 3 months ago, tolerance 21 days. Changes below 5% stay quiet, 5% or more is `watch`, and 10% or more is `attention`.
- Visit frequency: the last 7 days are compared with the previous 21 days normalized to a weekly count. The baseline must have at least 6 visits and at least 2 visits/week; changes below 40% stay quiet, 40% or more is `watch`, and 70% or more is `attention`.
- Unidentified visits: completed unidentified visits over the last 7 days signal at 3 visits as `watch` and 6 visits as `attention`.
- Stale device data: an unhealthy poller adds an `attention` data-quality signal.

The UI renders a compact dashboard signal area only when signals exist and shows at most the most relevant per-cat signal on cat cards. Copy is intentionally non-diagnostic and metadata carries the comparison values for explainability.
