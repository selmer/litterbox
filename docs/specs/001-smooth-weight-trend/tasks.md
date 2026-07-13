# Tasks: Smooth Weight Trend

**Input**: Design documents from `docs/specs/001-smooth-weight-trend/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/weight-chart-contract.md](./contracts/weight-chart-contract.md), [quickstart.md](./quickstart.md)

**Tests**: Automated frontend tests are required because the changed behavior is in the React weight chart presentation. Backend tests, migrations, and firmware checks are not required unless implementation changes `app/routers/visits.py`, `app/schemas.py`, persistence, or `/display/summary`.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing chart and API contract boundaries before changing behavior.

- [X] T001 Review the existing chart data transformation and Recharts test harness in `frontend/src/components/WeightChart.jsx` and `frontend/src/components/WeightChart.test.jsx`
- [X] T002 [P] Review the unchanged weight-history API client and response contract in `frontend/src/api/client.js` and `docs/specs/001-smooth-weight-trend/contracts/weight-chart-contract.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared chart-data structure needed by all user stories.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Update `frontend/src/components/WeightChart.jsx` chart-row construction to carry both displayed weight fields and original recorded weight context per cat series
- [X] T004 Update `frontend/src/components/WeightChart.test.jsx` baseline chart-data assertions so existing sorting, same-day, cross-year, visit-id, range, and tick-format behavior still passes with the expanded row shape

**Checkpoint**: Foundation ready - chart rows can represent smoothed display values without losing original measurement context.

---

## Phase 3: User Story 1 - View a Stable Weight Trend (Priority: P1) MVP

**Goal**: Display a smoother same-cat weight trend that reduces short-term measurement noise while preserving sustained gain/loss direction.

**Independent Test**: A noisy same-cat data set with at least 10 measurements produces fewer displayed direction reversals than the raw sequence, and a sustained 7-day gain/loss still has the correct displayed direction.

### Tests for User Story 1

- [X] T005 [US1] Add a noisy same-cat smoothing test in `frontend/src/components/WeightChart.test.jsx` that asserts displayed chart values have at least 50% fewer direction reversals than raw weights
- [X] T006 [US1] Add a sustained change test in `frontend/src/components/WeightChart.test.jsx` that asserts displayed chart values preserve the correct gain/loss direction over at least 7 days
- [X] T007 [US1] Add a multi-cat isolation test in `frontend/src/components/WeightChart.test.jsx` that asserts one cat's displayed trend is not influenced by another cat's measurements

### Implementation for User Story 1

- [X] T008 [US1] Implement deterministic per-cat presentation smoothing in `frontend/src/components/WeightChart.jsx` before cat series are merged into Recharts rows
- [X] T009 [US1] Preserve existing range controls, chronological sorting, `connectNulls`, legend behavior, and localized date formatting while integrating smoothed display values in `frontend/src/components/WeightChart.jsx`

**Checkpoint**: User Story 1 is independently testable as the MVP.

---

## Phase 4: User Story 2 - Preserve Measurement Context (Priority: P2)

**Goal**: Keep original recorded measurements available wherever the chart shows smoothed values.

**Independent Test**: A chart row for a smoothed point retains the recorded weight, visit id, timestamp, and confidence context needed for tooltip or detail display.

### Tests for User Story 2

- [X] T010 [US2] Add chart-data assertions in `frontend/src/components/WeightChart.test.jsx` proving each smoothed point retains original recorded weight and visit id context
- [X] T011 [US2] Add tooltip-context coverage in `frontend/src/components/WeightChart.test.jsx` proving displayed and recorded weight context can be distinguished when values differ

### Implementation for User Story 2

- [X] T012 [US2] Update `frontend/src/components/WeightChart.jsx` tooltip payload handling to expose recorded weight context alongside the displayed smoothed value
- [X] T013 [US2] Update `frontend/src/components/WeightChart.jsx` tooltip text so the user can identify the recorded weight and visit id without changing the existing API contract

**Checkpoint**: User Story 2 works independently with US1 chart data and does not require backend changes.

---

## Phase 5: User Story 3 - Handle Sparse or Irregular Data (Priority: P3)

**Goal**: Avoid misleading smoothed trends when data is sparse, gapped, missing, excluded, or irregular.

**Independent Test**: One-point and two-point histories remain unsmoothed, large gaps do not create invented intermediate certainty, and invalid/missing values do not corrupt displayed trend rows.

### Tests for User Story 3

- [X] T014 [US3] Add sparse-history tests in `frontend/src/components/WeightChart.test.jsx` proving one-point and two-point cat histories use recorded weights as displayed weights
- [X] T015 [US3] Add irregular-data tests in `frontend/src/components/WeightChart.test.jsx` covering large gaps, same-day repeated measurements, and non-finite or missing weight values

### Implementation for User Story 3

- [X] T016 [US3] Update `frontend/src/components/WeightChart.jsx` smoothing guards so cats with fewer than three usable measurements remain unsmoothed
- [X] T017 [US3] Update `frontend/src/components/WeightChart.jsx` data filtering and gap handling so invalid points are excluded and no invented timestamps or visits are added

**Checkpoint**: All user stories are independently functional and preserve the existing backend contract.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation consistency across all user stories.

- [X] T018 [P] Run the focused chart test command from `docs/specs/001-smooth-weight-trend/quickstart.md` against `frontend/src/components/WeightChart.test.jsx`
- [X] T019 [P] Run frontend lint from `docs/AGENTS.md` for `frontend/`
- [X] T020 [P] Run `npm audit` from `frontend/` and document any vulnerability findings in the final implementation report
- [X] T021 Run the full frontend test suite from `frontend/` after focused chart tests pass
- [X] T022 [P] Review `docs/specs/001-smooth-weight-trend/checklists/ux.md` and update `docs/specs/001-smooth-weight-trend/spec.md` only if implementation uncovered a requirements ambiguity

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion - MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational completion and integrates naturally after US1.
- **User Story 3 (Phase 5)**: Depends on Foundational completion and can be worked after or alongside US1/US2 if file conflicts are coordinated.
- **Polish (Phase 6)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 View a Stable Weight Trend**: Can start after Phase 2; no dependency on US2 or US3.
- **US2 Preserve Measurement Context**: Can start after Phase 2, but final tooltip wording depends on the row shape established for US1 smoothing.
- **US3 Handle Sparse or Irregular Data**: Can start after Phase 2, but guard behavior should be reconciled with US1 smoothing logic.

### Within Each User Story

- Write or update tests before implementation where practical.
- Keep original `weight_kg` values as recorded context before replacing any visible line value.
- Preserve the existing `/visits/weight-history` contract and date range behavior.
- Complete each story's tests before moving to the next priority.

## Parallel Opportunities

- T002 can run in parallel with T001.
- US1 test tasks T005, T006, and T007 target the same test file and should be sequenced by one editor, but they can be reasoned about independently.
- US2 and US3 touch the same component/test files as US1; they are conceptually independent but should not be edited concurrently in the same worktree.
- T018, T019, T020, and T022 can run in parallel after implementation if tooling and audit output are available.

## Parallel Example: User Story 1

```bash
Task: "Add noisy same-cat smoothing test in frontend/src/components/WeightChart.test.jsx"
Task: "Add sustained change test in frontend/src/components/WeightChart.test.jsx"
Task: "Add multi-cat isolation test in frontend/src/components/WeightChart.test.jsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tests T005-T007.
3. Complete US1 implementation T008-T009.
4. Run the focused chart test command from `docs/specs/001-smooth-weight-trend/quickstart.md`.
5. Stop and validate that the trend is smoother while sustained changes remain visible.

### Incremental Delivery

1. Deliver US1 for readable smoother trends.
2. Add US2 so users can inspect original recorded values behind the trend.
3. Add US3 so sparse and irregular histories avoid misleading smoothing.
4. Finish with lint, audit, focused tests, and full frontend regression tests.

### Contract Discipline

- Do not change `app/routers/visits.py`, `app/schemas.py`, migrations, backup/restore behavior, or firmware unless a new task is added with explicit spec and plan updates.
- If an API change becomes necessary, pause implementation and update `docs/specs/001-smooth-weight-trend/spec.md`, `docs/specs/001-smooth-weight-trend/plan.md`, and `docs/specs/001-smooth-weight-trend/contracts/weight-chart-contract.md` before continuing.

## Notes

- [P] tasks = different files or verification commands that do not depend on each other's file edits.
- [US1], [US2], and [US3] labels map tasks to user stories in `docs/specs/001-smooth-weight-trend/spec.md`.
- Tests are required because the feature changes chart behavior.
- Prefer verifying focused tests fail before implementing changed behavior.
