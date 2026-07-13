---

description: "Task list template for feature implementation"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED for changed behavior. Include backend pytest,
frontend Vitest/Testing Library, migration smoke, or contract tests according to the
feature's affected boundaries. Omit test tasks only when the spec explicitly states a
no-test rationale.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `app/`, `app/routers/`, `app/models.py`, `app/schemas.py`, `tests/`
- **Frontend**: `frontend/src/pages/`, `frontend/src/components/`, `frontend/src/api/`, `frontend/src/i18n/`
- **Database**: `alembic/versions/`
- **Firmware**: `firmware/epaper-display/`
- **Docs/specs**: `docs/`, `docs/specs/`

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize [language] project with [framework] dependencies
- [ ] T003 [P] Configure linting and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Identify affected FastAPI routes, frontend API calls, display/webhook/backup contracts, and legacy behavior in docs/specs/[###-feature]/plan.md
- [ ] T005 Create Alembic migration in alembic/versions/ if persistence changes are required
- [ ] T006 [P] Add or update backend pytest coverage in tests/ for changed API/domain/poller behavior
- [ ] T007 [P] Add or update frontend Vitest coverage in frontend/src/ for changed UI behavior
- [ ] T008 Add logging, diagnostics, health, or UI error-state coverage required by the constitution
- [ ] T009 Confirm secret/config/upload/archive handling for changed sensitive surfaces

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 1

> **NOTE: Required for changed behavior. Prefer writing tests before implementation
> and confirming they fail for the intended reason.**

- [ ] T010 [P] [US1] Backend route/domain test for [behavior] in tests/test_[name].py
- [ ] T011 [P] [US1] Frontend component/page test for [workflow] in frontend/src/[path]/[name].test.jsx

### Implementation for User Story 1

- [ ] T012 [P] [US1] Update schemas/models/helpers for [behavior] in app/[path].py
- [ ] T013 [US1] Implement API/domain behavior in app/routers/[resource].py or app/[domain].py
- [ ] T014 [US1] Update frontend API/client or page workflow in frontend/src/[path]
- [ ] T015 [US1] Add validation and error handling
- [ ] T016 [US1] Add logging, diagnostics, health state, or UI error state required for [behavior]
- [ ] T017 [US1] Update docs/specs or user documentation for contract/config changes

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 2

- [ ] T018 [P] [US2] Backend route/domain test for [behavior] in tests/test_[name].py
- [ ] T019 [P] [US2] Frontend component/page test for [workflow] in frontend/src/[path]/[name].test.jsx

### Implementation for User Story 2

- [ ] T020 [P] [US2] Update schemas/models/helpers for [behavior] in app/[path].py
- [ ] T021 [US2] Implement API/domain behavior in app/routers/[resource].py or app/[domain].py
- [ ] T022 [US2] Update frontend API/client or page workflow in frontend/src/[path]
- [ ] T023 [US2] Integrate with User Story 1 components (if needed)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - [Title] (Priority: P3)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Tests for User Story 3

- [ ] T024 [P] [US3] Backend route/domain test for [behavior] in tests/test_[name].py
- [ ] T025 [P] [US3] Frontend component/page test for [workflow] in frontend/src/[path]/[name].test.jsx

### Implementation for User Story 3

- [ ] T026 [P] [US3] Update schemas/models/helpers for [behavior] in app/[path].py
- [ ] T027 [US3] Implement API/domain behavior in app/routers/[resource].py or app/[domain].py
- [ ] T028 [US3] Update frontend API/client or page workflow in frontend/src/[path]

**Checkpoint**: All user stories should now be independently functional

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] Documentation updates in docs/
- [ ] TXXX Code cleanup and refactoring
- [ ] TXXX Performance optimization across all stories
- [ ] TXXX [P] Additional regression tests for legacy behavior in tests/
- [ ] TXXX [P] Frontend lint and relevant Vitest tests in frontend/
- [ ] TXXX Security/secrets review for changed admin/upload/webhook/diagnostics surfaces
- [ ] TXXX Migration smoke check with alembic upgrade head if schema changed
- [ ] TXXX Run quickstart.md validation and required merge commands

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests for changed behavior MUST be written before or with implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch tests for User Story 1 together:
Task: "Backend route/domain test for [behavior] in tests/test_[name].py"
Task: "Frontend component/page test for [workflow] in frontend/src/[path]/[name].test.jsx"

# Launch independent implementation tasks:
Task: "Update backend schema/helper in app/[path].py"
Task: "Update frontend component/page in frontend/src/[path]"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Prefer verifying tests fail before implementing changed behavior
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
