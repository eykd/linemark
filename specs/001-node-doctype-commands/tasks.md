# Tasks: Node and Document Type Operations

**Input**: Design documents from `/specs/001-node-doctype-commands/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: This feature follows Test-First Development (TDD) - all tests MUST be written and FAIL before implementation begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/linemark/`, `tests/` at repository root
- Paths follow existing linemark hexagonal architecture

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new domain exceptions needed across all user stories

- [X] T001 [P] Add InvalidRegexError exception to src/linemark/domain/exceptions.py
- [X] T002 [P] Add SearchError exception to src/linemark/domain/exceptions.py

**Checkpoint**: Domain exceptions ready for use in ports and use cases

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core ports and domain logic that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Port Protocols

- [X] T003 [P] Create ReadTypePort protocol in src/linemark/ports/read_type.py
- [X] T004 [P] Create WriteTypePort protocol in src/linemark/ports/write_type.py
- [X] T005 [P] Create SearchPort protocol with SearchResult model in src/linemark/ports/search.py

### Domain Logic (Search-Specific)

- [X] T006 Create search domain module in src/linemark/domain/search.py with helper functions for SQID extraction and pattern compilation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Read Document Type Content (Priority: P1) 🎯 MVP

**Goal**: Users can read the body content of a specific document type for a node (excluding YAML frontmatter)

**Independent Test**: Create a node with a doctype, write content to it, verify `lmk types read` returns exact body content

### Contract Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T007 [P] [US1] Contract test for ReadTypePort protocol in tests/contract/test_read_type_port.py
- [ ] T008 [P] [US1] Contract test for ReadTypeAdapter implementation in tests/contract/test_read_type_adapter.py

### Unit Tests for User Story 1

- [ ] T009 [US1] Unit test for ReadTypeUseCase in tests/unit/test_read_type_use_case.py

### Implementation for User Story 1

- [ ] T010 [US1] Implement ReadTypeAdapter in src/linemark/adapters/read_type_adapter.py (implements ReadTypePort, parses YAML frontmatter)
- [ ] T011 [US1] Implement ReadTypeUseCase in src/linemark/use_cases/read_type.py (orchestrates ReadTypePort)
- [ ] T012 [US1] Add `lmk types read` CLI command to src/linemark/cli/main.py with --directory option

### Integration Tests for User Story 1

- [ ] T013 [US1] End-to-end integration test for `lmk types read` command in tests/integration/test_types_read_workflow.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can read document type content via CLI.

---

## Phase 4: User Story 2 - Write Document Type Content (Priority: P2)

**Goal**: Users can write new body content to a document type file from stdin with atomic guarantees and frontmatter preservation

**Independent Test**: Pipe content to write command, verify file created/updated with correct body while preserving frontmatter

### Contract Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US2] Contract test for WriteTypePort protocol in tests/contract/test_write_type_port.py
- [ ] T015 [P] [US2] Contract test for WriteTypeAdapter implementation in tests/contract/test_write_type_adapter.py (verify atomic writes)

### Unit Tests for User Story 2

- [ ] T016 [US2] Unit test for WriteTypeUseCase in tests/unit/test_write_type_use_case.py

### Implementation for User Story 2

- [ ] T017 [US2] Implement WriteTypeAdapter in src/linemark/adapters/write_type_adapter.py (implements WriteTypePort with atomic write pattern: tempfile + os.replace)
- [ ] T018 [US2] Implement WriteTypeUseCase in src/linemark/use_cases/write_type.py (orchestrates WriteTypePort, handles stdin reading)
- [ ] T019 [US2] Add `lmk types write` CLI command to src/linemark/cli/main.py with --directory option and stdin handling

### Integration Tests for User Story 2

- [ ] T020 [US2] End-to-end integration test for `lmk types write` command in tests/integration/test_types_write_workflow.py (test create, update, empty stdin, frontmatter preservation, atomic write behavior)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can read and write document type content.

---

## Phase 5: User Story 3 - Search Across Nodes (Priority: P3)

**Goal**: Users can search for regex/literal patterns across the outline with filtering by subtree and doctype

**Independent Test**: Create multiple nodes with known content patterns, run search queries with filters, verify results match expected nodes in outline order

### Contract Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US3] Contract test for SearchPort protocol in tests/contract/test_search_port.py
- [ ] T022 [P] [US3] Contract test for SearchAdapter implementation in tests/contract/test_search_adapter.py (verify regex compilation, line-by-line matching, outline ordering)

### Unit Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for search domain logic in tests/unit/test_search_domain.py (pattern compilation, SQID extraction)
- [ ] T024 [US3] Unit test for SearchUseCase in tests/unit/test_search_use_case.py

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement SearchAdapter in src/linemark/adapters/search_adapter.py (implements SearchPort with regex matching, file iteration in outline order)
- [ ] T026 [US3] Implement SearchUseCase in src/linemark/use_cases/search.py (orchestrates SearchPort, handles result formatting for plaintext and JSON)
- [ ] T027 [US3] Add `lmk search` CLI command to src/linemark/cli/main.py with options: --doctype, --case-sensitive, --multiline, --literal, --json, --directory

### Integration Tests for User Story 3

- [ ] T028 [US3] End-to-end integration test for `lmk search` command in tests/integration/test_search_workflow.py (test basic search, subtree filter, doctype filter, case sensitivity, multiline, literal, JSON output)

**Checkpoint**: All user stories should now be independently functional. Users can read, write, and search document type content.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Quality improvements and documentation

- [ ] T029 [P] Run full test suite with coverage report: `./scripts/runtests.sh` - verify 100% coverage
- [ ] T030 [P] Run mypy type checking: `uv run mypy src/` - verify strict mode passes with no errors
- [ ] T031 [P] Run ruff linting: `uv run ruff check src/ tests/` - verify all rules pass
- [ ] T032 [P] Run ruff formatting: `uv run ruff format src/ tests/` - ensure consistent code style
- [ ] T033 Validate quickstart.md examples against actual CLI behavior
- [ ] T034 [P] Add docstrings (Google style) to all public APIs in ports, adapters, use cases
- [ ] T035 Performance profiling for search across 1000+ nodes (verify <5s target)
- [ ] T036 [P] Update CLAUDE.md if any patterns discovered during implementation
- [ ] T037 Code review: Verify hexagonal architecture boundaries (domain has no I/O dependencies)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 but may reference similar patterns
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2 but builds on same port pattern

### Within Each User Story (TDD Flow)

1. **Contract tests FIRST** → Write test for port protocol → Ensure FAILS
2. **Contract tests FIRST** → Write test for adapter implementation → Ensure FAILS
3. **Unit tests FIRST** → Write test for use case logic → Ensure FAILS
4. **Implementation** → Write minimal code to make tests PASS
5. **Integration tests** → Write end-to-end test → Ensure FAILS → Implement CLI → Tests PASS
6. **Refactor** → Clean up code while keeping tests green

### Parallel Opportunities

- Phase 1: Both T001 and T002 can run in parallel (different exceptions)
- Phase 2: T003, T004, T005 can all run in parallel (different port files)
- Within each user story:
  - Contract tests marked [P] can run in parallel
  - Unit tests marked [P] can run in parallel
  - Implementation in different files marked [P] can run in parallel
- Once Foundational completes, all three user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch contract tests in parallel:
Task: "Contract test for ReadTypePort protocol"
Task: "Contract test for ReadTypeAdapter implementation"

# After contract tests pass, launch implementation in parallel:
Task: "Implement ReadTypeAdapter" (one developer)
Task: "Implement ReadTypeUseCase" (another developer, once adapter exists)
```

---

## Parallel Example: All User Stories

```bash
# After Foundational phase completes, launch all user stories in parallel:
Developer A: Works on User Story 1 (Read) - T007 through T013
Developer B: Works on User Story 2 (Write) - T014 through T020
Developer C: Works on User Story 3 (Search) - T021 through T028

# Each story is independently testable and deployable
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T006) - CRITICAL - blocks all stories
3. Complete Phase 3: User Story 1 (T007-T013)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Run quality gates: tests, mypy, ruff
6. Deploy/demo `lmk types read` functionality

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP: read capability)
3. Add User Story 2 → Test independently → Deploy (read + write)
4. Add User Story 3 → Test independently → Deploy (read + write + search - full feature)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T006)
2. Once Foundational is done:
   - Developer A: User Story 1 (T007-T013) - Read operations
   - Developer B: User Story 2 (T014-T020) - Write operations
   - Developer C: User Story 3 (T021-T028) - Search operations
3. Stories complete and integrate independently
4. Run Phase 6 polish together

---

## Test-First Development Checklist

For EVERY task marked with a test:

- [ ] Write test FIRST
- [ ] Run test → Verify it FAILS (red)
- [ ] Write minimal implementation
- [ ] Run test → Verify it PASSES (green)
- [ ] Refactor if needed while keeping tests green
- [ ] Commit with message: "feat(US#): [description]"

For EVERY implementation task:

- [ ] Verify related tests exist and are failing
- [ ] Write minimal code to make tests pass
- [ ] Do not add code that isn't tested
- [ ] Keep test coverage at 100%

---

## Quality Gates (Before Completion)

All of these MUST pass before the feature is considered complete:

- [ ] All tests pass: `./scripts/runtests.sh`
- [ ] 100% test coverage: No untested code paths
- [ ] mypy strict mode: `uv run mypy src/` with zero errors
- [ ] ruff linting: `uv run ruff check src/ tests/` with zero violations
- [ ] ruff formatting: `uv run ruff format --check src/ tests/` passes
- [ ] All three user stories independently testable
- [ ] Quickstart.md examples validated against CLI
- [ ] No TODO comments in production code
- [ ] Hexagonal architecture maintained (domain has no I/O)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **RED-GREEN-REFACTOR**: Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constitution principle: Test-first is NON-NEGOTIABLE
- Use contracts/ directory specs as reference for port protocols
- Follow research.md for atomic write pattern and regex handling
- Use data-model.md for entity structure (SearchResult, etc.)
