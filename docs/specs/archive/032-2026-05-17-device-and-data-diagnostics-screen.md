# 032 - Device and Data Diagnostics Screen

## Summary

Create a diagnostics screen that gathers poller, Tuya, visit evidence, backend, and ESP32 display state in one place. The goal is to make debugging data weirdness fast and inspectable.

## Problem

When durations, weights, or display output look wrong, the operator currently has to inspect logs, API endpoints, and database state manually. Existing diagnostics are useful but scattered.

## Proposed Behavior

Add a Diagnostics page in the web app with sections for:

- Poller health and mode
- Last successful/attempted poll
- Last poll error
- Open visit state
- Recent visit diagnostics from spec 025
- Recent Tuya report-log reconciliation summary
- Display summary preview for ESP32
- Firmware/display last fetch info if available later

## Backend Scope

- Add `GET /diagnostics/summary` or equivalent.
- Include safe, redacted operational data only.
- Do not dump secrets, API keys, raw credentials, or full Tuya auth payloads.
- Include recent diagnostic events with visit ids and timestamps.
- Include open visit count and oldest open visit age.

## UI Scope

- Add Diagnostics navigation item or secondary link.
- Use dense but readable operational layout.
- Provide copyable snippets for relevant API endpoints or visit ids.
- Link from Visits rows to diagnostics for that visit when available.

## Acceptance Criteria

- Operator can determine poller freshness from the UI.
- Operator can see whether a visit is open/pending/hard-timed-out.
- Operator can inspect recent visit diagnostics without direct database access.
- Display summary can be previewed from the web UI.
- Sensitive values are not exposed.

## Test Plan

- Backend tests for diagnostics summary shape.
- Backend tests for redaction/no secret leakage.
- Frontend tests for diagnostics page states.
- Manual test using real odd visits and display summary.
