# 029 - Visit Correction Workflow

## Summary

Add a first-class workflow for correcting visit records from the web UI. Operators should be able to fix bad historical data without API calls or direct database edits.

## Problem

Bad visits currently require awkward workarounds. The Visits UI supports delete and reassign, but the backend only allows `cat_id` updates through `PATCH /visits/{id}`. If a visit has the wrong weight, timestamp, or duration, the operator cannot correct it in the app. This makes weight charts and e-paper comparisons less trustworthy.

## Proposed Behavior

- Add visit editing for:
  - `started_at`
  - `duration_seconds`
  - `weight_kg`
  - `cat_id`
  - optional `exclude_from_weight_history` if spec 030 is built together or later
- Derive `ended_at` from `started_at + duration_seconds` when duration is present.
- Preserve evidence metadata from spec 025; manual edits should be explicit and auditable.
- Make edit actions available from the Visits screen row/card.
- Keep delete as a separate destructive action.

## Backend Scope

- Extend `VisitUpdate` to accept editable fields.
- Validate bounds consistently with `VisitCreate`:
  - positive weight up to `MAX_CAT_WEIGHT_KG`
  - positive duration up to `MAX_VISIT_DURATION_SECONDS`
  - valid cat id or `null`
- Set `identified_by = manual` when cat is manually assigned.
- Set `duration_source = manual` and `duration_is_estimated = false` when duration is manually edited.
- Consider storing an edit diagnostic event if spec 025 diagnostics are available.

## UI Scope

- Add an Edit visit modal from Visits table/card actions.
- Fields:
  - cat selector including unidentified/visitor
  - date/time input
  - duration minutes/seconds or seconds input
  - weight kg input
- Show visit id in the modal for traceability.
- After successful edit, update the Visits list and refresh dependent chart/dashboard data.

## Acceptance Criteria

- Operator can edit visit time, duration, weight, and cat from the UI.
- Edited visit appears correctly in `/visits`, `/dashboard`, `/visits/weight-history`, and `/display/summary`.
- Invalid values are rejected with useful UI feedback.
- Manual edits do not silently masquerade as Tuya-measured evidence.
- Existing delete and reassign flows still work.

## Test Plan

- Backend tests for each editable field.
- Backend tests for invalid weight, invalid duration, unknown cat id, and `cat_id: null`.
- Backend tests that edited weight/date affect weight-history.
- Frontend tests for opening, submitting, validation failure, and successful modal update.
- Regression test that edited visits refresh dependent UI state.
