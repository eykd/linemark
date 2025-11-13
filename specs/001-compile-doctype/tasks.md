# Tasks: Compile Doctype Command

**Input**: Design documents from `/specs/001-compile-doctype/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Following TDD approach as mandated by constitution - all tests written BEFORE implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/linemark/`, `tests/` at repository root
- Tests organized by type: `tests/contract/`, `tests/unit/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify existing project structure matches plan.md expectations
- [x] T002 [P] Review existing FileSystem port in src/linemark/ports/filesystem.py
- [x] T003 [P] Review existing FileSystemAdapter in src/linemark/adapters/filesystem.py

---

## Phase 2: Foundational (Domain Exception)

**Purpose**: Core domain exception needed by all user stories

**⚠️ CRITICAL**: This exception is required before implementing any user story's use case

- [x] T004 Add DoctypeNotFoundError exception in src/linemark/domain/exceptions.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Compile Entire Forest by Doctype (Priority: P1) 🎯 MVP

**Goal**: Enable users to compile all content of a specific doctype from the entire forest into a single document

**Independent Test**: Run `lmk compile draft` on a forest with multiple nodes containing draft doctypes and verify output is concatenated in depth-first order

### Tests for User Story 1 (TDD - Write FIRST, Ensure FAIL)

> **CRITICAL**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T005 [P] [US1] Write contract test for CompileDoctypeUseCase constructor in tests/contract/test_compile_doctype_contract.py
- [ ] T006 [P] [US1] Write contract test for CompileDoctypeUseCase.execute signature in tests/contract/test_compile_doctype_contract.py
- [ ] T007 [P] [US1] Write contract test for DoctypeNotFoundError raising in tests/contract/test_compile_doctype_contract.py
- [ ] T008 [P] [US1] Write unit test for basic forest compilation in tests/unit/test_compile_doctype_unit.py
- [ ] T009 [P] [US1] Write unit test for skipping nodes without doctype in tests/unit/test_compile_doctype_unit.py
- [ ] T010 [P] [US1] Write unit test for skipping empty/whitespace files in tests/unit/test_compile_doctype_unit.py
- [ ] T011 [P] [US1] Write unit test for doctype not found error in tests/unit/test_compile_doctype_unit.py
- [ ] T012 [P] [US1] Write unit test for empty result handling in tests/unit/test_compile_doctype_unit.py

**Checkpoint**: All tests written and FAILING - ready for implementation

### Implementation for User Story 1

- [ ] T013 [US1] Create minimal CompileDoctypeUseCase class in src/linemark/use_cases/compile_doctype.py (constructor only)
- [ ] T014 [US1] Implement node collection logic (list_outline) in src/linemark/use_cases/compile_doctype.py
- [ ] T015 [US1] Implement doctype validation (pre-scan for existence) in src/linemark/use_cases/compile_doctype.py
- [ ] T016 [US1] Implement content collection (read files, check emptiness) in src/linemark/use_cases/compile_doctype.py
- [ ] T017 [US1] Implement separator processing (escape sequences) in src/linemark/use_cases/compile_doctype.py
- [ ] T018 [US1] Implement output concatenation logic in src/linemark/use_cases/compile_doctype.py
- [ ] T019 [US1] Add CLI command `lmk compile` in src/linemark/cli/main.py (basic doctype arg only)
- [ ] T020 [US1] Add error handling and exit codes in CLI command in src/linemark/cli/main.py
- [ ] T021 [US1] Add help text and docstring for compile command in src/linemark/cli/main.py

**Checkpoint**: Run contract and unit tests - all should PASS

### Integration Tests for User Story 1

- [ ] T022 [P] [US1] Write integration test for compiling multiple nodes in tests/integration/test_compile_doctype_integration.py
- [ ] T023 [P] [US1] Write integration test for skipping empty files in tests/integration/test_compile_doctype_integration.py
- [ ] T024 [P] [US1] Write integration test for doctype not found error in tests/integration/test_compile_doctype_integration.py
- [ ] T025 [P] [US1] Write integration test for empty result handling in tests/integration/test_compile_doctype_integration.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Basic `lmk compile draft` works for entire forest.

---

## Phase 4: User Story 2 - Compile Subtree by Doctype (Priority: P2)

**Goal**: Enable users to compile content from a specific subtree by providing a SQID identifier

**Independent Test**: Run `lmk compile draft SQID123` on a forest where SQID123 has children, and verify only that subtree's content appears in output

### Tests for User Story 2 (TDD - Write FIRST, Ensure FAIL)

> **CRITICAL**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T026 [P] [US2] Write unit test for subtree filtering logic in tests/unit/test_compile_doctype_unit.py
- [ ] T027 [P] [US2] Write unit test for invalid SQID error in tests/unit/test_compile_doctype_unit.py
- [ ] T028 [P] [US2] Write unit test for SQID with no matching doctype in tests/unit/test_compile_doctype_unit.py
- [ ] T029 [P] [US2] Write unit test for root node inclusion in subtree in tests/unit/test_compile_doctype_unit.py
- [ ] T030 [P] [US2] Write unit test for leaf node (no children) in tests/unit/test_compile_doctype_unit.py

**Checkpoint**: All tests written and FAILING - ready for implementation

### Implementation for User Story 2

- [ ] T031 [US2] Add SQID argument to CLI command in src/linemark/cli/main.py
- [ ] T032 [US2] Add SQID prefix stripping logic (@prefix handling) in src/linemark/cli/main.py
- [ ] T033 [US2] Implement subtree filtering in CompileDoctypeUseCase.execute in src/linemark/use_cases/compile_doctype.py
- [ ] T034 [US2] Add SQID validation (node exists) in src/linemark/use_cases/compile_doctype.py
- [ ] T035 [US2] Add NodeNotFoundError handling in CLI command in src/linemark/cli/main.py

**Checkpoint**: Run unit tests for US2 - all should PASS

### Integration Tests for User Story 2

- [ ] T036 [P] [US2] Write integration test for subtree compilation with children in tests/integration/test_compile_doctype_integration.py
- [ ] T037 [P] [US2] Write integration test for leaf node subtree in tests/integration/test_compile_doctype_integration.py
- [ ] T038 [P] [US2] Write integration test for invalid SQID error in tests/integration/test_compile_doctype_integration.py
- [ ] T039 [P] [US2] Write integration test for subtree with no matching doctype in tests/integration/test_compile_doctype_integration.py
- [ ] T040 [P] [US2] Write integration test for @ prefix stripping in tests/integration/test_compile_doctype_integration.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. `lmk compile draft` and `lmk compile draft @SQID` both work.

---

## Phase 5: User Story 3 - Custom Separator Between Documents (Priority: P3)

**Goal**: Enable users to customize the separator used between concatenated documents

**Independent Test**: Run `lmk compile draft --separator "===PAGE BREAK==="` and verify the custom separator appears between documents

### Tests for User Story 3 (TDD - Write FIRST, Ensure FAIL)

> **CRITICAL**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T041 [P] [US3] Write unit test for custom separator in tests/unit/test_compile_doctype_unit.py
- [ ] T042 [P] [US3] Write unit test for escape sequence interpretation (\n, \t) in tests/unit/test_compile_doctype_unit.py
- [ ] T043 [P] [US3] Write unit test for empty separator in tests/unit/test_compile_doctype_unit.py
- [ ] T044 [P] [US3] Write unit test for default separator when not provided in tests/unit/test_compile_doctype_unit.py

**Checkpoint**: All tests written and FAILING - ready for implementation

### Implementation for User Story 3

- [ ] T045 [US3] Add --separator option to CLI command in src/linemark/cli/main.py
- [ ] T046 [US3] Pass separator parameter to use case in CLI command in src/linemark/cli/main.py
- [ ] T047 [US3] Update CompileDoctypeUseCase.execute to accept separator parameter in src/linemark/use_cases/compile_doctype.py
- [ ] T048 [US3] Implement escape sequence interpretation (codecs.decode) in src/linemark/use_cases/compile_doctype.py
- [ ] T049 [US3] Update concatenation logic to use processed separator in src/linemark/use_cases/compile_doctype.py

**Checkpoint**: Run unit tests for US3 - all should PASS

### Integration Tests for User Story 3

- [ ] T050 [P] [US3] Write integration test for custom text separator in tests/integration/test_compile_doctype_integration.py
- [ ] T051 [P] [US3] Write integration test for escape sequence interpretation in tests/integration/test_compile_doctype_integration.py
- [ ] T052 [P] [US3] Write integration test for empty separator in tests/integration/test_compile_doctype_integration.py
- [ ] T053 [P] [US3] Write integration test for default separator in tests/integration/test_compile_doctype_integration.py

**Checkpoint**: All user stories should now be independently functional. Full feature complete!

---

## Phase 6: Polish & Quality Gates

**Purpose**: Enforce 100% quality standards across all user stories

- [ ] T054 [P] Add --directory option to CLI command in src/linemark/cli/main.py
- [ ] T055 [P] Write integration test for custom directory in tests/integration/test_compile_doctype_integration.py
- [ ] T056 Run full test suite with coverage: `uv run pytest tests/ -v --cov`
- [ ] T057 Verify 100% test coverage achieved - add missing tests if needed
- [ ] T058 Run mypy type checking: `uv run mypy src/` - fix all errors
- [ ] T059 Run ruff linting: `uv run ruff check src/ tests/` - fix all violations
- [ ] T060 Run ruff formatting: `uv run ruff format src/ tests/`
- [ ] T061 [P] Update CLI help text for accuracy in src/linemark/cli/main.py
- [ ] T062 [P] Verify error messages are user-friendly (per CLI contract)
- [ ] T063 Manual testing: Run quickstart.md test scenarios
- [ ] T064 Code review readiness check (no TODOs, FIXMEs, debug code)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories are designed to be independent and can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Builds on US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Builds on US1 but independently testable

**Note**: US2 and US3 enhance US1 functionality but don't break it. Each story adds incremental value.

### Within Each User Story (TDD Cycle)

1. Write ALL tests for the story FIRST
2. Verify tests FAIL (red phase)
3. Implement minimal code to pass tests
4. Verify tests PASS (green phase)
5. Refactor if needed
6. Write integration tests
7. Verify end-to-end functionality

### Parallel Opportunities

**Within Phase 1 (Setup)**:
- T002 and T003 can run in parallel (different files)

**Within Phase 2 (Foundational)**:
- Only T004 (single file addition)

**Within User Story 1 - Tests**:
- T005-T012 can all run in parallel (different test functions)

**Within User Story 1 - Integration Tests**:
- T022-T025 can all run in parallel (different test cases)

**Within User Story 2 - Tests**:
- T026-T030 can all run in parallel (different test functions)

**Within User Story 2 - Integration Tests**:
- T036-T040 can all run in parallel (different test cases)

**Within User Story 3 - Tests**:
- T041-T044 can all run in parallel (different test functions)

**Within User Story 3 - Integration Tests**:
- T050-T053 can all run in parallel (different test cases)

**Within Phase 6 (Polish)**:
- T054, T055, T061, T062 can run in parallel (different files/concerns)

**Across User Stories** (if team capacity allows):
- After Foundation completes, US1, US2, US3 can be developed in parallel by different developers
- Each story has independent tests and implementation tasks
- Integration happens naturally since US2/US3 extend US1 without breaking it

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all contract/unit tests for User Story 1 together:
Task: "Write contract test for CompileDoctypeUseCase constructor"
Task: "Write contract test for CompileDoctypeUseCase.execute signature"
Task: "Write contract test for DoctypeNotFoundError raising"
Task: "Write unit test for basic forest compilation"
Task: "Write unit test for skipping nodes without doctype"
Task: "Write unit test for skipping empty/whitespace files"
Task: "Write unit test for doctype not found error"
Task: "Write unit test for empty result handling"

# All 8 tests can be written in parallel (different test functions)
```

---

## Parallel Example: User Story 1 Integration Tests

```bash
# Launch all integration tests for User Story 1 together:
Task: "Write integration test for compiling multiple nodes"
Task: "Write integration test for skipping empty files"
Task: "Write integration test for doctype not found error"
Task: "Write integration test for empty result handling"

# All 4 tests can be written in parallel (different test scenarios)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003) - ~15 min
2. Complete Phase 2: Foundational (T004) - ~15 min
3. Write ALL tests for US1 (T005-T012) - ~30 min
4. Implement US1 (T013-T021) - ~90 min
5. Write integration tests for US1 (T022-T025) - ~30 min
6. **STOP and VALIDATE**: Test User Story 1 independently
7. **MVP READY**: Basic `lmk compile draft` works!

**Total MVP Time**: ~3 hours (following strict TDD)

### Incremental Delivery

1. **Week 1**: Complete Setup + Foundational + US1 → MVP deployed (basic compilation)
2. **Week 2**: Add US2 → Test independently → Deploy (subtree support added)
3. **Week 3**: Add US3 → Test independently → Deploy (custom separators added)
4. **Week 4**: Polish phase → Quality gates → Final release

Each week delivers working, testable functionality without breaking previous features.

### Parallel Team Strategy

With 3 developers after Foundation completes:

1. **Team**: Complete Setup + Foundational together (~30 min)
2. **Split work**:
   - Developer A: User Story 1 (core feature) - ~3 hours
   - Developer B: User Story 2 (subtree support) - ~2 hours
   - Developer C: User Story 3 (custom separators) - ~1.5 hours
3. **Merge**: US1 first, then US2, then US3
4. **Polish**: All together (~1 hour)

**Total Parallel Time**: ~4-5 hours (vs ~6-7 hours sequential)

---

## Task Statistics

**Total Tasks**: 64
- Phase 1 (Setup): 3 tasks
- Phase 2 (Foundational): 1 task
- Phase 3 (US1): 21 tasks (8 contract/unit tests, 9 implementation, 4 integration tests)
- Phase 4 (US2): 15 tasks (5 unit tests, 5 implementation, 5 integration tests)
- Phase 5 (US3): 13 tasks (4 unit tests, 5 implementation, 4 integration tests)
- Phase 6 (Polish): 11 tasks

**Test Coverage**:
- Contract tests: 3 (T005-T007)
- Unit tests: 14 (T008-T012, T026-T030, T041-T044)
- Integration tests: 13 (T022-T025, T036-T040, T050-T053, T055)
- **Total test tasks**: 30 (47% of all tasks - TDD emphasis)

**Parallel Opportunities**: 34 tasks marked [P] (53% parallelizable)

**MVP Scope**: Tasks T001-T025 (39% of total tasks delivers working MVP)

---

## Notes

- **[P] tasks**: Different files, no dependencies - can run in parallel
- **[Story] label**: Maps task to specific user story for traceability and independent testing
- **TDD Mandatory**: All tests written BEFORE implementation (constitution requirement)
- **100% Coverage Required**: No exceptions (constitution requirement)
- **Each user story**: Independently completable and testable
- **Verify tests fail**: CRITICAL before implementing (red-green-refactor cycle)
- **Commit frequency**: After each logical group or checkpoint
- **Stop at checkpoints**: Validate story independently before proceeding
- **Quality gates**: Phase 6 enforces mypy strict, ruff zero violations, 100% coverage

**Estimated Total Implementation Time**: 4-6 hours (sequential), 3-4 hours (parallel with 3 developers)
