# API Domain Validation and Referential Integrity

Priority: P1

Problem:
Pydantic schemas in `app/schemas.py:8-56` accept broad primitive types without domain constraints. Visit creation in `app/routers/visits.py:14-27` accepts any `cat_id`, duration, timestamp, and weight. Visit reassignment in `app/routers/visits.py:112-124` can set `identified_by` and does not validate target cat existence. Cat creation and update in `app/routers/cats.py:30-64` accept blank names and any reference weight value.

Current behavior:

- Negative or unrealistic weights can be accepted by API schemas.
- Manual visits can reference nonexistent cats.
- `identified_by` can be client-controlled on visit update.
- `offset` lacks an explicit non-negative query constraint in `app/routers/visits.py:30-43`.

Proposed behavior:

- Add schema constraints for names, weights, durations, limits, offsets, and timestamps.
- Validate `cat_id` on manual visit creation and reassignment.
- Treat `identified_by` as server-owned except for explicit, documented admin operations.
- Return consistent 400 or 422 errors with actionable messages.

Acceptance criteria:

- Blank cat names are rejected.
- Negative, zero, or unrealistic weights and durations are rejected according to documented bounds.
- Nonexistent `cat_id` values are rejected on visit creation and reassignment.
- Reassigning a visit to `null` deliberately marks it as visitor/unidentified using documented semantics.

Verification:

- Add backend API tests for invalid cats, invalid visits, invalid pagination, and reassignment edge cases.
- Confirm frontend validation messages match backend constraints.
