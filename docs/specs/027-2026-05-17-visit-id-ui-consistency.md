# 027 - Visit ID UI Consistency

## Summary

Make visit identifiers available consistently where they are useful for diagnosing suspicious weight-chart points, without turning the everyday UI into a database console.

Spec 026 added `Visit #<id>` to the weight-chart tooltip so an operator can identify which visit backs a chart point. This creates a small UI consistency gap: the Visits screen currently shows an `ID` column, but that column actually contains identification status badges such as `auto`, `manual`, or `unidentified` instead of the visit id.

## Problem

When the chart tooltip exposes a visit id, the operator needs a natural place to cross-check that id in the Visits screen. Today, the Visits table has a misleading `ID` header because it shows the identification method rather than the persisted visit id.

This makes debugging possible but slightly awkward: a chart point can say `Visit #36`, while the Visits screen does not expose `#36` as a first-class visible value.

## Current Behavior

- Weight-chart tooltip can show `Visit #<id>` for hovered points.
- Visits table has an `ID` column, but its cells render `auto`, `manual`, or `unidentified` badges.
- Mobile visit cards show the identification badge, but not the visit id.
- Visit ids are available in API data as `visit.id`.

## Proposed Behavior

- Show visit ids on the Visits screen as subtle, structural metadata.
- Rename or split the misleading table columns:
  - use `ID` for the actual visit id, displayed as `#36`
  - use `Source` or `Identified` for the existing `auto` / `manual` / `unidentified` badge
- Add the visit id to mobile visit cards in a compact metadata position.
- Keep the chart tooltip visit id as secondary diagnostic metadata, not a primary visual element.
- Do not add prominent visit ids to dashboard cards or top-level summaries.

## UX Guidelines

- Visit ids should be visible enough for debugging, but visually quieter than cat, date, weight, and duration.
- Use monospace or muted metadata styling if it matches existing table/card conventions.
- Avoid adding another loud badge style; the id is stable reference metadata, not a state.
- Keep mobile layout compact and prevent the id from crowding primary visit details.

## Acceptance Criteria

- A chart tooltip value such as `Visit #36` can be found directly on the Visits screen.
- The Visits table no longer labels identification badges as `ID`.
- Desktop table shows both the actual visit id and identification source/status.
- Mobile visit cards expose the actual visit id.
- Existing reassign and delete actions remain unchanged.
- No backend/API changes are required.

## Verification

- Frontend tests for `VisitsList` confirm visit id rendering on desktop and mobile representations.
- Existing Visits page tests still pass.
- `npm run lint`
- `npm test`
- Optional visual check in light-professional and dark-elegant themes.

## Relationship To Other Specs

- Builds on spec 026, which made chart points traceable to `visit_id`.
- Complements spec 022, which redesigned the Visits screen, by correcting a metadata labeling inconsistency.
- Does not implement full visit field editing; that remains a possible follow-up under spec 026 or a future dedicated spec.

## Assumptions

- Visit ids are useful primarily for diagnosis and support, not everyday monitoring.
- Showing ids in a quiet metadata style is preferable to removing them from the chart tooltip.
- The existing Visits API already returns the required `id` field.
