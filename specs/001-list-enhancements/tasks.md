# Tasks: Enhanced List Command with Subtree Filtering and Metadata Display

**Input**: Design documents from `/specs/001-list-enhancements/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/list_command.md, quickstart.md

**Tests**: Tests are MANDATORY per project constitution (Test-First Development principle). All tests must be written BEFORE implementation and must FAIL before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project structure: `src/linemark/`, `tests/` at repository root
- Follow existing hexagonal architecture: domain, ports, adapters, use_cases, cli

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure is ready for feature development

- [X] T001 Verify test environment runs successfully with existing tests: `./scripts/runtests.sh`
- [X] T002 [P] Verify mypy strict mode passes on existing code: `uv run mypy src/`
- [X] T003 [P] Verify ruff linting passes on existing code: `uv run ruff check src/ tests/`
- [X] T004 Review existing `ListOutlineUseCase` in `src/linemark/use_cases/list_outline.py` to understand current implementation
- [X] T005 [P] Review existing formatters in `src/linemark/cli/formatters.py` to understand tree/JSON output
- [X] T006 [P] Review existing CLI command in `src/linemark/cli/main.py` to understand current `lmk list` interface

**Checkpoint**: Development environment verified, existing code understood

---

## Phase 2: Foundational (No Blocking Prerequisites)

**Purpose**: This feature extends existing functionality - no foundational work needed

✅ **SKIPPED**: All required infrastructure (domain entities, ports, adapters) already exists

**Checkpoint**: Ready to begin user story implementation immediately

---

## Phase 3: User Story 1 - Subtree Filtering by SQID (Priority: P1) 🎯 MVP

**Goal**: Users can filter outline view to a specific subtree by providing a SQID argument

**Independent Test**: Run `lmk list <sqid>` and verify only that subtree is displayed

### Tests for User Story 1 (MANDATORY - Write FIRST, ensure they FAIL)

- [X] T007 [P] [US1] Write unit test for `ListOutlineUseCase.execute()` with valid SQID filtering to subtree in `tests/unit/test_list_outline_use_case.py`
- [X] T008 [P] [US1] Write unit test for `ListOutlineUseCase.execute()` with leaf node SQID returning single node in `tests/unit/test_list_outline_use_case.py`
- [X] T009 [P] [US1] Write unit test for `ListOutlineUseCase.execute()` with invalid SQID raising ValueError in `tests/unit/test_list_outline_use_case.py`
- [X] T010 [P] [US1] Write unit test for `ListOutlineUseCase.execute()` with orphaned SQID returning single node in `tests/unit/test_list_outline_use_case.py`
- [X] T011 [P] [US1] Write unit test for `ListOutlineUseCase.execute()` with SQID returning all nodes (backward compatibility) in `tests/unit/test_list_outline_use_case.py`
- [X] T012 [US1] Run tests and confirm they FAIL with expected messages: `pytest tests/unit/test_list_outline_use_case.py -v`

### Implementation for User Story 1

- [X] T013 [US1] Add optional `root_sqid` parameter to `ListOutlineUseCase.execute()` method in `src/linemark/use_cases/list_outline.py`
- [X] T014 [US1] Implement `_filter_to_subtree()` private method in `src/linemark/use_cases/list_outline.py`
- [X] T015 [US1] Implement `_is_orphaned()` private method for orphan detection in `src/linemark/use_cases/list_outline.py`
- [X] T016 [US1] Implement `_get_subtree()` private method for descendant filtering in `src/linemark/use_cases/list_outline.py`
- [X] T017 [US1] Run unit tests and confirm they PASS: `pytest tests/unit/test_list_outline_use_case.py -v`
- [X] T018 [US1] Update CLI `list()` function to accept optional SQID argument in `src/linemark/cli/main.py`
- [X] T019 [US1] Pass SQID argument to `ListOutlineUseCase.execute()` in `src/linemark/cli/main.py`
- [X] T020 [US1] Add error handling for ValueError from invalid SQID in `src/linemark/cli/main.py`

### Integration Tests for User Story 1

- [X] T021 [P] [US1] Write integration test for `lmk list <sqid>` command filtering to subtree in `tests/integration/test_list_command_integration.py`
- [X] T022 [P] [US1] Write integration test for `lmk list <invalid>` command showing error in `tests/integration/test_list_command_integration.py`
- [X] T023 [P] [US1] Write integration test for `lmk list` without args (backward compatibility) in `tests/integration/test_list_command_integration.py`
- [X] T024 [US1] Run integration tests and confirm they PASS: `pytest tests/integration/test_list_command_integration.py::test_*us1* -v`

### Quality Gates for User Story 1

- [X] T025 [US1] Run all tests for User Story 1: `pytest tests/unit/test_list_outline_use_case.py tests/integration/test_list_command_integration.py -v`
- [X] T026 [US1] Verify 100% coverage for new code: `pytest --cov=linemark.use_cases.list_outline --cov=linemark.cli.main --cov-report=term-missing`
- [X] T027 [US1] Run mypy strict mode: `uv run mypy src/linemark/use_cases/list_outline.py src/linemark/cli/main.py`
- [X] T028 [US1] Run ruff linting: `uv run ruff check src/linemark/use_cases/ src/linemark/cli/`
- [X] T029 [US1] Format code: `uv run ruff format src/linemark/use_cases/ src/linemark/cli/`
- [X] T030 [US1] Manual test: `lmk list` shows full outline (backward compatibility)
- [X] T031 [US1] Manual test: `lmk list <valid-sqid>` shows only subtree
- [X] T032 [US1] Manual test: `lmk list <invalid>` shows error message

**Checkpoint**: User Story 1 (Subtree Filtering) is complete and independently functional. MVP is ready!

---

## Phase 4: User Story 2 - Display Doctypes in Outline (Priority: P2)

**Goal**: Users can see document types for each node using `--show-doctypes` flag

**Independent Test**: Run `lmk list --show-doctypes` and verify doctypes are displayed

### Tests for User Story 2 (MANDATORY - Write FIRST, ensure they FAIL)

- [X] T033 [P] [US2] Write unit test for `format_tree()` with `show_doctypes=True` displaying doctypes in `tests/unit/test_formatters.py`
- [X] T034 [P] [US2] Write unit test for `format_tree()` with `show_doctypes=True` omitting empty metadata in `tests/unit/test_formatters.py`
- [X] T035 [P] [US2] Write unit test for `format_tree()` with multiple doctypes as comma-separated list in `tests/unit/test_formatters.py`
- [X] T036 [P] [US2] Write unit test for `format_json()` with `show_doctypes=True` adding doctypes field in `tests/unit/test_formatters.py`
- [X] T037 [P] [US2] Write unit test for `format_json()` with `show_doctypes=True` omitting doctypes field when empty in `tests/unit/test_formatters.py`
- [X] T038 [P] [US2] Write unit test for `format_tree()` with `show_doctypes=False` (backward compatibility) in `tests/unit/test_formatters.py`
- [X] T039 [US2] Run tests and confirm they FAIL with expected messages: `pytest tests/unit/test_formatters.py -v`

### Implementation for User Story 2

- [X] T040 [US2] Add optional `show_doctypes` parameter (default False) to `format_tree()` in `src/linemark/cli/formatters.py`
- [X] T041 [US2] Implement doctype metadata line generation in `format_tree()` in `src/linemark/cli/formatters.py`
- [X] T042 [US2] Add proper tree indentation for doctype metadata lines in `src/linemark/cli/formatters.py`
- [X] T043 [US2] Implement comma-separated doctype formatting (sorted alphabetically) in `src/linemark/cli/formatters.py`
- [X] T044 [US2] Add optional `show_doctypes` parameter (default False) to `format_json()` in `src/linemark/cli/formatters.py`
- [X] T045 [US2] Implement conditional doctypes field addition in JSON output in `src/linemark/cli/formatters.py`
- [X] T046 [US2] Run unit tests and confirm they PASS: `pytest tests/unit/test_formatters.py -v`
- [X] T047 [US2] Add `--show-doctypes` CLI flag to `list()` command in `src/linemark/cli/main.py`
- [X] T048 [US2] Pass `show_doctypes` parameter to formatters in `src/linemark/cli/main.py`

### Integration Tests for User Story 2

- [X] T049 [P] [US2] Write integration test for `lmk list --show-doctypes` showing doctypes in tree output in `tests/integration/test_list_command_integration.py`
- [X] T050 [P] [US2] Write integration test for `lmk list --show-doctypes --json` including doctypes field in `tests/integration/test_list_command_integration.py`
- [X] T051 [P] [US2] Write integration test combining SQID and --show-doctypes: `lmk list <sqid> --show-doctypes` in `tests/integration/test_list_command_integration.py`
- [X] T052 [US2] Run integration tests and confirm they PASS: `pytest tests/integration/test_list_command_integration.py::test_*us2* -v`

### Quality Gates for User Story 2

- [X] T053 [US2] Run all tests for User Story 2: `pytest tests/unit/test_formatters.py tests/integration/test_list_command_integration.py::test_*doctypes* -v`
- [X] T054 [US2] Verify 100% coverage for new code: `pytest --cov=linemark.cli.formatters --cov-report=term-missing`
- [X] T055 [US2] Run mypy strict mode: `uv run mypy src/linemark/cli/formatters.py`
- [X] T056 [US2] Run ruff linting: `uv run ruff check src/linemark/cli/`
- [X] T057 [US2] Format code: `uv run ruff format src/linemark/cli/`
- [X] T058 [US2] Manual test: `lmk list --show-doctypes` displays doctypes on indented lines
- [X] T059 [US2] Manual test: `lmk list --show-doctypes --json` includes doctypes field
- [X] T060 [US2] Manual test: `lmk list` without flag works (backward compatibility)

**Checkpoint**: User Stories 1 AND 2 are both independently functional

---

## Phase 5: User Story 3 - Display File Paths in Outline (Priority: P3)

**Goal**: Users can see file paths for each node using `--show-files` flag

**Independent Test**: Run `lmk list --show-files` and verify file paths are displayed

### Tests for User Story 3 (MANDATORY - Write FIRST, ensure they FAIL)

- [X] T061 [P] [US3] Write unit test for `format_tree()` with `show_files=True` displaying file paths in `tests/unit/test_formatters.py`
- [X] T062 [P] [US3] Write unit test for `format_tree()` with `show_files=True` omitting when no files in `tests/unit/test_formatters.py`
- [X] T063 [P] [US3] Write unit test for `format_tree()` with multiple files showing all paths in `tests/unit/test_formatters.py`
- [X] T064 [P] [US3] Write unit test for `format_tree()` with long paths showing full path in `tests/unit/test_formatters.py`
- [X] T065 [P] [US3] Write unit test for `format_json()` with `show_files=True` adding files field in `tests/unit/test_formatters.py`
- [X] T066 [P] [US3] Write unit test for `format_json()` with `show_files=True` omitting files field when empty in `tests/unit/test_formatters.py`
- [X] T067 [US3] Run tests and confirm they FAIL with expected messages: `pytest tests/unit/test_formatters.py -v`

### Implementation for User Story 3

- [X] T068 [US3] Add optional `show_files` parameter (default False) to `format_tree()` in `src/linemark/cli/formatters.py`
- [X] T069 [US3] Add optional `directory` parameter for file path computation to `format_tree()` in `src/linemark/cli/formatters.py`
- [X] T070 [US3] Implement file path metadata line generation using `node.filenames()` in `src/linemark/cli/formatters.py`
- [X] T071 [US3] Add proper tree indentation for file path metadata lines (one per file) in `src/linemark/cli/formatters.py`
- [X] T072 [US3] Add optional `show_files` and `directory` parameters to `format_json()` in `src/linemark/cli/formatters.py`
- [X] T073 [US3] Implement conditional files field addition in JSON output in `src/linemark/cli/formatters.py`
- [X] T074 [US3] Run unit tests and confirm they PASS: `pytest tests/unit/test_formatters.py -v`
- [X] T075 [US3] Add `--show-files` CLI flag to `list()` command in `src/linemark/cli/main.py`
- [X] T076 [US3] Pass `show_files` and `directory` parameters to formatters in `src/linemark/cli/main.py`

### Integration Tests for User Story 3

- [X] T077 [P] [US3] Write integration test for `lmk list --show-files` showing file paths in tree output in `tests/integration/test_list_command_integration.py`
- [X] T078 [P] [US3] Write integration test for `lmk list --show-files --json` including files field in `tests/integration/test_list_command_integration.py`
- [X] T079 [P] [US3] Write integration test combining SQID and --show-files: `lmk list <sqid> --show-files` in `tests/integration/test_list_command_integration.py`
- [X] T080 [US3] Run integration tests and confirm they PASS: `pytest tests/integration/test_list_command_integration.py::test_*us3* -v`

### Quality Gates for User Story 3

- [X] T081 [US3] Run all tests for User Story 3: `pytest tests/unit/test_formatters.py tests/integration/test_list_command_integration.py::test_*files* -v`
- [X] T082 [US3] Verify 100% coverage maintained: `pytest --cov=linemark.cli.formatters --cov-report=term-missing`
- [X] T083 [US3] Run mypy strict mode: `uv run mypy src/linemark/cli/formatters.py`
- [X] T084 [US3] Run ruff linting: `uv run ruff check src/linemark/cli/`
- [X] T085 [US3] Format code: `uv run ruff format src/linemark/cli/`
- [X] T086 [US3] Manual test: `lmk list --show-files` displays file paths on indented lines
- [X] T087 [US3] Manual test: `lmk list --show-files --json` includes files field
- [X] T088 [US3] Manual test: Long file paths display without truncation

**Checkpoint**: User Stories 1, 2, AND 3 are all independently functional

---

## Phase 6: User Story 4 - Combined Flags (Priority: P3)

**Goal**: Users can combine SQID argument with multiple flags for comprehensive view

**Independent Test**: Run `lmk list <sqid> --show-doctypes --show-files --json` and verify all features work together

### Integration Tests for User Story 4 (Tests for combined functionality)

- [X] T089 [P] [US4] Write integration test for `lmk list --show-doctypes --show-files` combining both flags in tree output in `tests/integration/test_list_command_integration.py`
- [X] T090 [P] [US4] Write integration test for `lmk list <sqid> --show-doctypes --show-files` combining all features in tree in `tests/integration/test_list_command_integration.py`
- [X] T091 [P] [US4] Write integration test for `lmk list --show-doctypes --show-files --json` combining both flags in JSON in `tests/integration/test_list_command_integration.py`
- [X] T092 [P] [US4] Write integration test for `lmk list <sqid> --show-doctypes --show-files --json` (all features) in `tests/integration/test_list_command_integration.py`
- [X] T093 [US4] Run integration tests and confirm they PASS: `pytest tests/integration/test_list_command_integration.py::test_*us4* -v`

### Implementation for User Story 4

**Note**: No new implementation needed - this validates that existing implementations work together correctly

- [X] T094 [US4] Verify formatters handle both show_doctypes and show_files simultaneously without conflicts
- [X] T095 [US4] Verify metadata lines appear in correct order (doctypes first, then files) in tree output
- [X] T096 [US4] Verify JSON output includes both fields when both flags are enabled

### Quality Gates for User Story 4

- [X] T097 [US4] Run full integration test suite: `pytest tests/integration/test_list_command_integration.py -v`
- [X] T098 [US4] Manual test: `lmk list --show-doctypes --show-files` displays both metadata types
- [X] T099 [US4] Manual test: `lmk list <sqid> --show-doctypes --show-files` filters and shows metadata
- [X] T100 [US4] Manual test: `lmk list --show-doctypes --show-files --json` includes both fields
- [X] T101 [US4] Manual test: Performance check with 100-node outline under 3 seconds

**Checkpoint**: All user stories complete and working together

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final quality checks and documentation

- [X] T102 Run complete test suite: `./scripts/runtests.sh`
- [X] T103 Verify 100% test coverage across all modified files: `pytest --cov=linemark --cov-report=html --cov-report=term-missing`
- [X] T104 [P] Run mypy strict on entire codebase: `uv run mypy src/`
- [X] T105 [P] Run ruff linting on entire codebase: `uv run ruff check src/ tests/`
- [X] T106 [P] Format entire codebase: `uv run ruff format src/ tests/`
- [X] T107 Update CLI help text and docstrings if needed in `src/linemark/cli/main.py`
- [X] T108 [P] Verify backward compatibility: Run existing tests to ensure no regressions
- [X] T109 Performance validation: Test with 100-node outline, verify < 3 second target
- [X] T110 [P] Update CLAUDE.md if new patterns were introduced (unlikely for this feature)
- [X] T111 Review quickstart.md validation checklist completion

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Skipped - no blocking prerequisites
- **User Story 1 (Phase 3)**: Can start immediately after Setup
- **User Story 2 (Phase 4)**: Can start after Setup - Independent of US1
- **User Story 3 (Phase 5)**: Can start after Setup - Independent of US1 and US2
- **User Story 4 (Phase 6)**: Requires US1, US2, and US3 complete (validates integration)
- **Polish (Phase 7)**: Requires all desired user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies - can start after Setup
- **User Story 2 (P2)**: No dependencies - can start after Setup (parallel with US1)
- **User Story 3 (P3)**: No dependencies - can start after Setup (parallel with US1/US2)
- **User Story 4 (P3)**: Depends on US1, US2, US3 (integration validation)

### Within Each User Story (TDD Workflow)

1. **Tests FIRST**: Write all unit tests, ensure they FAIL
2. **Implementation**: Write minimal code to make tests PASS
3. **Integration Tests**: Write and run integration tests
4. **Quality Gates**: Run coverage, mypy, ruff, manual tests
5. **Checkpoint**: Verify story is independently functional before proceeding

### Parallel Opportunities

**Setup Phase** (All can run in parallel):
- T002 (mypy verification) || T003 (ruff verification)
- T005 (review formatters) || T006 (review CLI)

**User Story Tests** (All tests within a story can be written in parallel):
- US1: T007, T008, T009, T010, T011 can all be written simultaneously
- US2: T033, T034, T035, T036, T037, T038 can all be written simultaneously
- US3: T061, T062, T063, T064, T065, T066 can all be written simultaneously
- US4: T089, T090, T091, T092 can all be written simultaneously

**User Stories** (Can be worked on in parallel by different developers):
- After Setup completes, US1, US2, and US3 can all proceed in parallel
- Different team members can own different user stories

**Polish Phase** (Some tasks can run in parallel):
- T104 (mypy) || T105 (ruff) || T106 (format) || T108 (backward compat tests)

---

## Parallel Example: User Story 2

```bash
# Launch all unit tests for User Story 2 together:
Task: "Write unit test for format_tree() with show_doctypes=True"
Task: "Write unit test for format_tree() omitting empty metadata"
Task: "Write unit test for format_tree() with multiple doctypes"
Task: "Write unit test for format_json() with show_doctypes=True"
Task: "Write unit test for format_json() omitting doctypes field"
Task: "Write unit test for format_tree() with show_doctypes=False"

# After tests written and fail, implement in parallel across files:
# (But in this case, both modifications are in same file, so sequential)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Skip Phase 2: Foundational (no blocking prerequisites)
3. Complete Phase 3: User Story 1 (T007-T032)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - MVP delivers subtree filtering capability!

**MVP Deliverable**: Users can run `lmk list <sqid>` to view any subtree

### Incremental Delivery

1. **Setup** → Development environment ready
2. **+US1 (MVP)** → Subtree filtering works → Test independently → Deploy/Demo
3. **+US2** → Add doctype display → Test independently → Deploy/Demo
4. **+US3** → Add file path display → Test independently → Deploy/Demo
5. **+US4** → Validate all features work together → Deploy/Demo
6. **+Polish** → Final quality checks and documentation

Each user story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers (after Setup completes):

**Strategy A - Parallel Stories**:
- Developer A: User Story 1 (T007-T032)
- Developer B: User Story 2 (T033-T060)
- Developer C: User Story 3 (T061-T088)
- All converge for User Story 4 integration validation

**Strategy B - Sequential (Recommended)**:
- Deliver US1 first (MVP)
- Then US2 (adds value to MVP)
- Then US3 (adds more value)
- Then US4 (validates integration)
- Enables faster feedback and incremental value delivery

---

## Summary

**Total Tasks**: 111 tasks
- Setup: 6 tasks
- Foundational: 0 tasks (skipped)
- User Story 1 (P1): 26 tasks (MVP)
- User Story 2 (P2): 28 tasks
- User Story 3 (P3): 28 tasks
- User Story 4 (P3): 13 tasks (integration validation)
- Polish: 10 tasks

**Task Breakdown by Story**:
- US1 (Subtree Filtering): 26 tasks including 6 unit tests, 3 integration tests, 8 quality gates
- US2 (Show Doctypes): 28 tasks including 7 unit tests, 3 integration tests, 8 quality gates
- US3 (Show Files): 28 tasks including 7 unit tests, 3 integration tests, 8 quality gates
- US4 (Combined Flags): 13 tasks including 4 integration tests, 5 quality gates

**Parallel Opportunities**:
- 24 tasks marked [P] can run in parallel within their phases
- 3 user stories (US1, US2, US3) can be developed in parallel after Setup
- All unit tests within a story can be written in parallel
- All integration tests within a story can be written in parallel

**Independent Test Criteria**:
- US1: `lmk list <sqid>` displays only subtree
- US2: `lmk list --show-doctypes` displays doctypes for each node
- US3: `lmk list --show-files` displays file paths for each node
- US4: `lmk list <sqid> --show-doctypes --show-files --json` all features work together

**Suggested MVP Scope**: User Story 1 only (subtree filtering)

**Estimated Timeline**:
- Setup: 1 hour
- US1 (MVP): 3-4 hours
- US2: 3-4 hours
- US3: 3-4 hours
- US4: 1-2 hours
- Polish: 1 hour
- **Total**: 12-16 hours for complete feature (7-10 hours for MVP only)

---

## Notes

- All tasks follow TDD: Write tests FIRST, confirm they FAIL, then implement
- [P] tasks = different files or independent operations, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Stop at any checkpoint to validate story independently
- 100% test coverage is MANDATORY per project constitution
- All code must pass mypy strict mode and ruff linting
- Backward compatibility must be maintained (existing usage unchanged)
