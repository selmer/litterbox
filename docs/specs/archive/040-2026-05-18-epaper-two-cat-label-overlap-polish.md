# 040 - E-Paper Two-Cat Label Overlap Polish

## Summary
Fix the visual overlap between the cat name `Griezeltje` and the `latest` label in the two-cat e-paper layout. This is a small firmware layout polish, not a backend/API redesign.

## Key Changes
- Adjust the two-cat row layout in the e-paper firmware so `Griezeltje` and `latest` no longer overlap.
- Prefer a small vertical spacing adjustment: move the metric labels/value block slightly downward within each row.
- Keep the existing 400x300 landscape layout and current two-row structure.
- Keep the current assumption that no cat names longer than `Griezeltje` need to fit in this pass.
- Do not change `/display/summary` or backend display data.

## Public Interfaces
- No backend API changes.
- No database migration.
- Firmware rendering only.

## Test Plan
- PlatformIO build succeeds for the e-paper firmware.
- Manual/photo verification with two cats shows no overlap between `Griezeltje` and `latest`.
- `Plurk` row remains readable.
- `latest`, `1m`, `3m`, visits count, values, deltas, and sparkline remain inside each row box.

## Assumptions
- The current e-paper layout is otherwise acceptable.
- A small vertical text-position adjustment is preferred over truncating `Griezeltje` further or redesigning columns.
