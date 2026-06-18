# Diagnostics Scan and Payload Disclosure

Priority: P2

Implementation scope:
Frontend Diagnostics page and related styles/tests. This spec makes diagnostics easier to scan while keeping raw payloads available for debugging.

## Summary

- Keep Diagnostics detailed and operator-oriented.
- Make recent diagnostic events easier to scan before reading raw JSON.
- Collapse or summarize payloads by default.
- Add explicit copy affordances for raw payloads where useful.

## Problem

Diagnostics currently exposes valuable raw data, including JSON payload snippets. That is useful for debugging, but it makes the screen visually noisy:

- payloads dominate table rows.
- mobile stacked rows become long quickly.
- important facts such as visit id, event type, recorded time, and status compete with raw JSON.

Operators should be able to scan the page first, then expand or copy raw data when investigating a specific issue.

## Current Behavior

- `frontend/src/pages/Diagnostics.jsx` renders stat cards, open visits, display summary, recent diagnostics, and useful endpoints.
- `JsonSnippet` renders full formatted JSON inside a `pre` with max height.
- Recent diagnostics table includes payload JSON directly in the row.
- Endpoint rows include a copy button for paths.

## Proposed Behavior

Change Diagnostics event presentation to a progressive-disclosure model:

- Show a compact event summary by default:
  - visit id
  - event type
  - recorded timestamp
  - one-line payload summary when possible
- Provide an expand/collapse control per event to reveal full JSON.
- Provide `Copy payload` for expanded payloads.
- Preserve highlighting for `?visit=<id>` deep links.
- On mobile, use diagnostic event cards rather than payload-heavy stacked rows.

Payload summaries should be simple and safe:

- Prefer known keys like `source`, `duration_source`, `weight_kg`, `reason`, `error`, or `status` when present.
- Fall back to a compact key-count summary, for example `5 fields`.
- Do not hide the raw JSON permanently.

## Implementation Notes

- Update `DiagnosticsEvent` in `frontend/src/pages/Diagnostics.jsx`.
- Consider extracting:
  - `PayloadSummary`
  - `ExpandableJsonPayload`
  - `DiagnosticsEventCard`
- Reuse the existing `CopyButton` pattern.
- Add translations for:
  - expand payload
  - collapse payload
  - copy payload
  - payload field summary if needed.
- Update CSS in `frontend/src/App.css`.
- Coordinate with spec `051` if both are implemented together:
  - diagnostics events should use the standardized responsive data strategy.

## Non-Goals

- Do not change diagnostics API response shape.
- Do not remove raw payload access.
- Do not add server-side payload summaries in this spec.
- Do not add filtering/search unless a future spec calls for it.
- Do not change endpoint copy behavior.

## Acceptance Criteria

- Recent diagnostic events are scannable without reading full JSON.
- Full payload JSON is available by expanding an event.
- Payload can be copied from the UI.
- `?visit=<id>` highlighting still works.
- Mobile layout does not show huge JSON blocks by default.
- Empty and no-recent-events states still render correctly.
- Existing Diagnostics stat cards and endpoint list remain available.

## Verification Plan

- Update `frontend/src/pages/Diagnostics.test.jsx` for:
  - compact event rendering.
  - expand/collapse payload.
  - copy payload button presence.
  - highlighted visit behavior.
  - empty diagnostics events state.
- Run `npm run lint` in `frontend/`.
- Run `npm test` in `frontend/`.
- Manually verify:
  - recent events with short payloads.
  - recent events with long nested payloads.
  - mobile layout.
  - light and dark themes.

## Rollback Notes

No backend or data change is involved. Rollback restores always-visible JSON snippets in the Diagnostics events table.
