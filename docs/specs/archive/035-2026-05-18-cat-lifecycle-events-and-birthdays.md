# 035 - Cat Lifecycle Events and Birthdays

## Summary

Add individual cat detail pages with a lightweight lifecycle timeline. Each cat gets an optional birthday/profile date, visible on the Cats overview, and a per-cat events list for vet visits, medication, diet changes, milestones, notes, and other significant moments.

## Key Changes

- Add nullable `birth_date` to cats and expose it through cat create/update/read APIs.
- Add `cat_events` with event type, occurrence timestamp, title, notes, optional cost, currency, and audit timestamps.
- Add cat event CRUD endpoints under `/cats/{cat_id}/events`.
- Add `/cats/:catId` frontend detail page with profile context, generated birthday row, event form, and event table.
- Show birthday/age context on the Cats overview while keeping full lifecycle details on the detail page.

## Acceptance Criteria

- Cat birthdays can be saved and displayed.
- Events can be created, edited, listed newest first, and deleted for a cat.
- Vet/event costs can be stored optionally with currency.
- The birthday timeline row is derived from `Cat.birth_date` and is not duplicated in `cat_events`.
- Empty and error states remain usable.

## Verification Plan

- Backend tests for `birth_date`, event CRUD, event validation, missing cats, and sort order.
- Frontend tests for Cats overview birthday/link behavior and Cat detail event workflows.
- Run backend py_compile, backend cat API tests, and frontend Cats tests.
