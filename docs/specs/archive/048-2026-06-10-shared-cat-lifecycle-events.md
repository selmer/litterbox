# 048 - Shared Cat Lifecycle Events

## Summary

Allow the operator to create one lifecycle event that applies to multiple cats, while keeping the event itself stored once in the database. The first UI entry point can remain an individual cat detail page: when adding an event for one cat, the form can optionally include other cats that the same event applies to.

## Problem

The current cat lifecycle event model is per-cat: `cat_events.cat_id` points at exactly one cat, and `/cats/{cat_id}/events` lists only rows owned by that cat. With two cats, many real-world events apply to both cats at once, for example a shared vet visit, household diet change, medication routine, grooming appointment, vaccination reminder, or moving-home milestone.

Duplicating those events per cat creates drift risk:

- Titles, notes, costs, and dates can accidentally diverge.
- Editing one copy does not update the other.
- Backup/restore and timeline review contain duplicate-looking records.
- Cost and note history becomes harder to trust.

The operator wants shared events to remain a single database event, shown on each affected cat page.

## Current Behavior

- `CatEvent` in `app/models.py` has a required `cat_id` foreign key.
- Cat event API endpoints live under `/cats/{cat_id}/events` in `app/routers/cats.py`.
- `CatDetail.jsx` fetches events for one cat and creates events only for that cat.
- `CatEventOut` exposes a single `cat_id`.

## Proposed Behavior

A lifecycle event can be linked to one or more cats. The event row stores the shared event content once; a join table stores which cats it appears under.

Initial UI behavior:

- Keep creation on the individual cat detail page.
- The add/edit form includes a compact multi-select or checkbox list of active cats.
- The current cat is selected by default and cannot accidentally be omitted when creating from that cat page unless the user deliberately edits the selection in an edit workflow.
- Saving creates or updates one shared event, not one event per selected cat.
- Each selected cat page shows the same event in its timeline.
- Event rows visually indicate when an event is shared, for example `Shared with Plurk` or `2 cats`.

Editing behavior:

- Editing shared event content updates it everywhere it appears.
- Editing the cat selection changes only the event-to-cat links.
- Deleting from a cat page should ask whether to:
  - remove the event only from this cat, if more than one cat is linked; or
  - delete the shared event entirely.
- For the first implementation, a simpler acceptable version is: delete always deletes the shared event globally, but the UI copy must make that explicit before deletion.

## Data Model

Add a join table, for example `cat_event_cats`:

- `event_id`: foreign key to `cat_events.id`, cascade delete
- `cat_id`: foreign key to `cats.id`, cascade delete
- unique constraint on `(event_id, cat_id)`
- index on `(cat_id, event_id)` for per-cat timelines

Keep `cat_events` as the canonical event content table. Existing events must be backfilled into the join table so every existing row remains visible on the same cat page.

Compatibility choice:

- Keep `cat_events.cat_id` during the first migration as `primary_cat_id` semantics for backward compatibility and deterministic ownership/context.
- New code should use the join table for visibility.
- API responses may keep `cat_id` for backward compatibility, but should add `cat_ids` and optionally `cat_names`.

A later cleanup can rename or remove `cat_id` if the compatibility field becomes unnecessary.

## API Scope

Update schemas:

- `CatEventCreate`
  - Add optional `cat_ids: list[int]`.
  - If omitted, default to `[path cat_id]`.
  - Validate all cats exist.
  - Validate the path cat is included, or document and enforce the chosen behavior.
- `CatEventUpdate`
  - Add optional `cat_ids: list[int]`.
  - Empty list is invalid.
- `CatEventOut`
  - Keep existing fields.
  - Add `cat_ids: list[int]`.
  - Add `cat_names: list[str]` if useful for UI labels.

Endpoint behavior:

- `GET /cats/{cat_id}/events` returns events linked through `cat_event_cats`, not only events where `cat_events.cat_id == cat_id`.
- `POST /cats/{cat_id}/events` creates one `CatEvent` and one link per selected cat.
- `PATCH /cats/{cat_id}/events/{event_id}` updates shared content and, if provided, selected cat links.
- `DELETE /cats/{cat_id}/events/{event_id}` follows the chosen delete semantics from the UI section.

## UI Scope

On `CatDetail.jsx`:

- Load active cats, or receive enough cat context from an API response, so the event form can show a cat selector.
- Default selection to the current cat.
- Show shared event context in the timeline row.
- Make edit behavior clear: changing title/notes/date/cost changes the event for all linked cats.
- If delete is global in the first pass, show copy such as `Delete this event for all linked cats`.

Copy should stay practical and calm; this is household recordkeeping, not a complex medical workflow.

## Migration Notes

- Create `cat_event_cats`.
- Backfill one link for every existing `cat_events` row using its current `cat_id`.
- Add constraints after backfill if needed.
- No existing event content should be duplicated.
- Backup/restore should include the new join table.

## Acceptance Criteria

- A shared event can be created once from a cat page and linked to both cats.
- The event appears on every linked cat detail page.
- Editing shared event content updates the same event everywhere.
- Existing single-cat events remain visible after migration.
- API responses expose enough linked-cat metadata for the UI to explain shared events.
- The database contains one event row for a shared event, plus link rows; it does not create duplicate event rows per cat.
- Tests cover single-cat events, shared two-cat events, edit behavior, delete behavior, and migration backfill.

## Test Plan

Backend:

- Migration test/backfill assertion for existing `cat_events.cat_id` rows.
- Create event with omitted `cat_ids` defaults to the path cat.
- Create event with two `cat_ids` stores one `CatEvent` and two join rows.
- List events for either linked cat returns the shared event.
- Updating event content through one cat endpoint is visible through the other cat endpoint.
- Invalid `cat_ids`, unknown cats, and empty selections are rejected.
- Delete semantics are covered explicitly.

Frontend:

- Cat event form defaults to current cat selected.
- Selecting another active cat creates a shared event.
- Timeline shows shared context.
- Editing a shared event preserves selected cats unless changed.
- Delete confirmation/copy matches the implemented delete behavior.

Manual:

- Add a shared vet visit for both cats from `/cats/1`.
- Verify it appears on `/cats/1` and `/cats/2`.
- Edit the notes from `/cats/2` and verify `/cats/1` shows the same updated notes.
- Confirm database has one event row and two link rows.


## Implementation Notes

Built with a new `cat_event_cats` join table and a compatibility-preserving `cat_events.cat_id` primary/context cat. Existing event rows are backfilled into the join table by migration `f0a1b2c3d4e5`.

Implemented delete semantics for the first pass are global: deleting a shared event removes the single event row and all links. The cat detail UI shows confirmation copy for shared events before doing this.

The cat detail form remains the only UI entry point. It now loads cats, defaults the current cat to selected, allows additional cats to be checked, and shows shared context in timeline rows.
