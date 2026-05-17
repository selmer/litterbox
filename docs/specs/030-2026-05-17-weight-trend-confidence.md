# 030 - Weight Trend Confidence

## Summary

Introduce confidence states for visit weights so obvious outliers can be reviewed or excluded from trend views without deleting the underlying visit.

## Problem

A single bad weight reading can distort the dashboard chart and e-paper comparisons. Deleting the visit removes useful visit history too. The app needs a way to keep the visit while treating its weight as suspect or ignored for trend calculations.

## Proposed Behavior

- Add weight confidence/status to visits:
  - `normal`
  - `suspect`
  - `ignored`
- Default new valid weights to `normal`.
- Automatically mark extreme outliers as `suspect` using simple per-cat heuristics.
- Allow the operator to manually set confidence from the Visits screen.
- Exclude `ignored` weights from trend charts and e-paper comparisons by default.
- Show suspect points in chart tooling or diagnostics without making them primary.

## Data Model

Add fields to `visits`:

- `weight_confidence` string, default `normal`
- optional `weight_confidence_reason` string

Potential reasons:

- `manual`
- `outlier_delta`
- `operator_ignored`
- `operator_restored`

## Backend Scope

- Update visit create/update schemas.
- Update weight-history query to exclude `ignored` by default.
- Consider `include_ignored=true` query param for diagnostics.
- Update display summary comparisons to exclude ignored weights.
- Add outlier detection during poller visit close or weight assignment.

## UI Scope

- Visits screen shows confidence state subtly.
- Visit edit/correction flow can mark weight as ignored/restored.
- Weight chart can optionally show suspect/ignored diagnostics later, but v1 may simply exclude ignored points.

## Acceptance Criteria

- Ignored weights no longer affect dashboard chart or e-paper comparisons.
- Suspect weights remain visible enough to review.
- Operator can mark a weight ignored without deleting the visit.
- Operator can restore an ignored weight.
- Existing historical visits default safely to `normal` during migration.

## Test Plan

- Migration test or schema verification for defaults.
- API tests for normal/suspect/ignored states.
- Weight-history tests that ignored weights are excluded by default.
- Display summary tests that ignored weights are excluded from latest/comparison data.
- Frontend tests for confidence controls.
