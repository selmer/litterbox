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
