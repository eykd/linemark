# Implementation Tasks: Linemark

**Feature**: Linemark - Hierarchical Markdown Outline Manager
**Branch**: `001-linemark-cli-mvp`
**Generated**: 2025-11-12

## Overview

This document provides a complete, executable task breakdown for implementing Linemark following test-first development (TDD) as mandated by the constitution. Tasks are organized by user story to enable independent implementation and incremental delivery.

**Implementation Strategy**: Inside-out hexagonal architecture (Domain → Ports → Adapters → Use Cases → CLI), with strict TDD discipline (Red-Green-Refactor).

---

## Task Summary

- **Total Tasks**: 72
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 15 tasks (blocking prerequisites)
- **User Story 1 (P1)**: 12 tasks
- **User Story 2 (P2)**: 8 tasks
- **User Story 3 (P2)**: 6 tasks
- **User Story 4 (P3)**: 6 tasks
- **User Story 5 (P3)**: 8 tasks
- **User Story 6 (P4)**: 4 tasks
- **User Story 7 (P4)**: 4 tasks
- **User Story 8 (P4)**: 4 tasks

**Parallelization Opportunities**: 45 tasks marked [P] can run in parallel within their phases.

**Independent Test Criteria**: Each user story phase includes verification steps to confirm the story works end-to-end before proceeding to the next.

---

## Phase 1: Setup & Project Initialization

**Goal**: Establish project structure, dependencies, and development environment per constitution requirements.

### Tasks

- [x] T001 Create project directory structure in src/linemark/ with subdirectories: domain/, ports/, adapters/, use_cases/, cli/
- [x] T002 Create test directory structure in tests/ with subdirectories: contract/, unit/, integration/
- [x] T003 Create pyproject.toml with dependencies: click>=8.1.8, sqids>=0.5.0, pyyaml>=6.0.2, python-slugify>=8.0.0, pydantic>=2.11.4, pytest>=8.3.5, pytest-cov, pytest-mock, mypy>=1.15.0, ruff>=0.11.8
- [x] T004 Configure ruff in pyproject.toml with comprehensive ruleset (all standard rules, strict docstrings, type annotations, security checks per constitution)
- [x] T005 Configure mypy in pyproject.toml with strict mode (no implicit optional, no untyped defs, pydantic plugin enabled per constitution)

**Validation**: Run `pip install -e .` and verify all dependencies install correctly.

---

## Phase 2: Foundational Layer (Domain + Ports)

**Goal**: Build pure domain logic and port definitions before any infrastructure. These are blocking prerequisites for all user stories.

**Constitutional Principle**: Domain logic must have zero dependencies (§ I Hexagonal Architecture).

### Domain Value Objects & Entities

- [X] T006 Write test for MaterializedPath.from_string() in tests/unit/test_entities.py
- [X] T007 Implement MaterializedPath value object in src/linemark/domain/entities.py with segments tuple, depth property, as_string property
- [X] T008 [P] Write test for MaterializedPath.parent() in tests/unit/test_entities.py
- [X] T009 [P] Implement MaterializedPath.parent() method returning parent path or None for root
- [X] T010 [P] Write test for MaterializedPath.child(position) in tests/unit/test_entities.py
- [X] T011 [P] Implement MaterializedPath.child(position) method creating child path
- [X] T012 [P] Write test for MaterializedPath validation (segments 1-999) in tests/unit/test_entities.py
- [X] T013 [P] Implement MaterializedPath field validator ensuring segments are 001-999
- [X] T014 [P] Write test for SQID value object in tests/unit/test_entities.py
- [X] T015 [P] Implement SQID value object in src/linemark/domain/entities.py with alphanumeric validation
- [X] T016 [P] Write test for Node entity creation in tests/unit/test_entities.py
- [X] T017 [P] Implement Node entity in src/linemark/domain/entities.py with sqid, mp, title, slug, document_types fields
- [X] T018 [P] Write test for Node.filename() generation in tests/unit/test_entities.py
- [X] T019 [P] Implement Node.filename(doc_type) method generating filename per FR-030 pattern
- [X] T020 [P] Write test for Outline aggregate in tests/unit/test_entities.py (includes validate_invariants and find_next_sibling_position)

### Port Definitions

- [X] T021 [P] Create FileSystemPort protocol in src/linemark/ports/filesystem.py with read_file, write_file, delete_file, rename_file, list_markdown_files, file_exists, create_directory methods
- [X] T022 [P] Create SQIDGeneratorPort protocol in src/linemark/ports/sqid_generator.py with encode, decode methods
- [X] T023 [P] Create SlugifierPort protocol in src/linemark/ports/slugifier.py with slugify method

**Validation**: Run `pytest tests/unit/ --cov=src/linemark/domain --cov=src/linemark/ports` and verify 100% coverage on domain and ports.

---

## Phase 3: User Story 1 - Create and Organize Outline Nodes (P1)

**Story Goal**: Writers can quickly build hierarchical outlines by adding chapters, sections, and subsections with meaningful titles while the system handles organizational details.

**Independent Test Criteria**:
- ✅ User can run `lmk add "Chapter One"` in empty directory
- ✅ Two files created: `001_<sqid>_draft_chapter-one.md` and `001_<sqid>_notes_chapter-one.md`
- ✅ Draft file contains YAML frontmatter with `title: Chapter One`
- ✅ User can run `lmk add --child-of @<sqid> "Section 1.1"`
- ✅ Child node created with MP like `001-100_<sqid>_draft_section-1-1.md`
- ✅ User can run `lmk list` and see tree hierarchy with titles

### Contract Tests for Adapters

- [X] T024 [P] [US1] Write contract test for FileSystemAdapter in tests/contract/test_filesystem_adapter.py verifying read_file, write_file methods
- [X] T025 [P] [US1] Implement FileSystemAdapter in src/linemark/adapters/filesystem.py using pathlib
- [X] T026 [P] [US1] Write contract test for SQIDGeneratorAdapter in tests/contract/test_sqid_adapter.py verifying encode/decode
- [X] T027 [P] [US1] Implement SQIDGeneratorAdapter in src/linemark/adapters/sqid_generator.py wrapping sqids library
- [X] T028 [P] [US1] Write contract test for SlugifierAdapter in tests/contract/test_slugifier_adapter.py verifying slugify
- [X] T029 [P] [US1] Implement SlugifierAdapter in src/linemark/adapters/slugifier.py wrapping python-slugify

### Domain Logic for Node Addition

- [X] T030 [US1] Implement Outline.find_next_sibling_position() in src/linemark/domain/entities.py using tiered numbering (100/10/1)
- [X] T031 [US1] Write test for Outline.add_node() in tests/unit/test_outline.py
- [X] T032 [US1] Implement Outline.add_node() method in src/linemark/domain/entities.py

### Use Case Implementation

- [X] T033 [US1] Write unit test for AddNodeUseCase with fake adapters in tests/unit/test_add_node_use_case.py
- [X] T034 [US1] Implement AddNodeUseCase in src/linemark/use_cases/add_node.py orchestrating domain logic with ports
- [X] T035 [US1] Write unit test for ListOutlineUseCase with fake adapters in tests/unit/test_list_outline_use_case.py
- [X] T036 [US1] Implement ListOutlineUseCase in src/linemark/use_cases/list_outline.py with tree rendering

### CLI Implementation

- [X] T037 [US1] Implement tree formatter in src/linemark/cli/formatters.py using depth-first traversal with Unicode box-drawing characters
- [X] T038 [US1] Create Click CLI group in src/linemark/cli/main.py with lmk command
- [X] T039 [US1] Implement `lmk add` command in src/linemark/cli/main.py with --child-of, --sibling-of, --before, --after, --directory options
- [X] T040 [US1] Implement `lmk list` command in src/linemark/cli/main.py with --json, --directory options

### Integration Test

- [X] T041 [US1] Write integration test in tests/integration/test_add_workflow.py verifying complete add → list workflow with real filesystem

**Story 1 Validation**: Run integration test. User should be able to add nodes and list outline in tree format.

---

## Phase 4: User Story 2 - Reorganize Content Structure (P2)

**Story Goal**: Writers can restructure outlines by moving sections to different locations without losing work or manually renaming files.

**Independent Test Criteria**:
- ✅ User can create multi-level outline (root → child → grandchild)
- ✅ User can run `lmk move @<sqid> --to @<parent-sqid>`
- ✅ Node and all descendants relocated with updated materialized paths
- ✅ SQIDs preserved across move
- ✅ All files renamed correctly, no data loss

### Domain Logic for Move Operations

- [X] T042 [P] [US2] Write test for MaterializedPath prefix replacement in tests/unit/test_entities.py
- [X] T043 [P] [US2] Write test for Outline.move_node() in tests/unit/test_outline.py
- [X] T044 [US2] Implement Outline.move_node() in src/linemark/domain/entities.py updating MPs for node and descendants

### Use Case Implementation

- [X] T045 [US2] Write unit test for MoveNodeUseCase with fake adapters in tests/unit/test_move_node_use_case.py
- [X] T046 [US2] Implement MoveNodeUseCase in src/linemark/use_cases/move_node.py with batch atomic rename per research.md R7

### CLI Implementation

- [X] T047 [US2] Implement `lmk move` command in src/linemark/cli/main.py with --to, --before, --after, --directory options

### Integration Test

- [X] T048 [US2] Write integration test in tests/integration/test_move_workflow.py verifying node move with 10+ descendants preserves data and hierarchy

**Story 2 Validation**: Run integration test. User should be able to move nodes with children and see updated hierarchy.

---

## Phase 5: User Story 3 - Maintain Multiple Document Types (P2)

**Story Goal**: Writers can keep different content types associated with each node (draft, notes, character sheets, etc.).

**Independent Test Criteria**:
- ✅ User can run `lmk types list @<sqid>` and see draft + notes
- ✅ User can run `lmk types add characters @<sqid>`
- ✅ New file created: `<mp>_<sqid>_characters_<slug>.md`
- ✅ User can run `lmk types remove characters @<sqid>`
- ✅ Only characters file deleted, draft and notes preserved

### Use Case Implementation

- [X] T049 [P] [US3] Write unit test for ManageTypesUseCase.list() in tests/unit/test_manage_types_use_case.py
- [X] T050 [P] [US3] Implement ManageTypesUseCase.list_types() in src/linemark/use_cases/manage_types.py
- [X] T051 [P] [US3] Write unit test for ManageTypesUseCase.add() in tests/unit/test_manage_types_use_case.py
- [X] T052 [P] [US3] Implement ManageTypesUseCase.add_type() in src/linemark/use_cases/manage_types.py
- [X] T053 [P] [US3] Write unit test for ManageTypesUseCase.remove() in tests/unit/test_manage_types_use_case.py
- [X] T054 [P] [US3] Implement ManageTypesUseCase.remove_type() in src/linemark/use_cases/manage_types.py with required type protection

### CLI Implementation

- [X] T055 [US3] Implement `lmk types` command group in src/linemark/cli/main.py with list, add, remove subcommands

### Integration Test

- [X] T056 [US3] Write integration test in tests/integration/test_types_workflow.py verifying add/remove types preserves draft and notes

**Story 3 Validation**: Run integration test. User should be able to manage document types without affecting required files.

---

## Phase 6: User Story 4 - Rename Nodes (P3)

**Story Goal**: Writers can refine node titles and have filenames automatically stay synchronized.

**Independent Test Criteria**:
- ✅ User can run `lmk rename @<sqid> "New Title"`
- ✅ Frontmatter title updated in draft file
- ✅ All filenames for node updated with new slug
- ✅ SQID preserved unchanged

### Use Case Implementation

- [X] T057 [P] [US4] Write unit test for RenameNodeUseCase in tests/unit/test_rename_node_use_case.py
- [X] T058 [US4] Implement RenameNodeUseCase in src/linemark/use_cases/rename_node.py updating frontmatter and renaming all document type files

### CLI Implementation

- [X] T059 [US4] Implement `lmk rename` command in src/linemark/cli/main.py with SQID/MP selector and new title

### Integration Test

- [X] T060 [US4] Write integration test in tests/integration/test_rename_workflow.py verifying rename with special characters and multiple document types

**Story 4 Validation**: Run integration test. User should be able to rename nodes and see updated filenames.

---

## Phase 7: User Story 5 - Remove Unwanted Content (P3)

**Story Goal**: Writers can clean up outlines by removing abandoned sections with options to delete or promote children.

**Independent Test Criteria**:
- ✅ User can run `lmk delete @<sqid>` on leaf node and confirm deletion
- ✅ All files for node deleted permanently
- ✅ User can run `lmk delete @<sqid> -r` on node with children
- ✅ Node and all descendants deleted
- ✅ User can run `lmk delete @<sqid> -p` on node with children
- ✅ Node deleted, children promoted to parent level with renumbered MPs

### Domain Logic for Delete Operations

- [X] T061 [P] [US5] Write test for Outline.delete_node() in tests/unit/test_outline.py
- [X] T062 [P] [US5] Write test for Outline.delete_node_recursive() in tests/unit/test_outline.py
- [X] T063 [P] [US5] Write test for Outline.delete_node_promote() in tests/unit/test_outline.py

### Use Case Implementation

- [X] T064 [US5] Implement Outline.delete_node() in src/linemark/domain/entities.py for leaf node deletion
- [X] T065 [US5] Implement Outline.delete_node_recursive() in src/linemark/domain/entities.py cascading deletion to descendants
- [X] T066 [US5] Implement Outline.delete_node_promote() in src/linemark/domain/entities.py promoting children and renumbering
- [X] T067 [US5] Write unit test for DeleteNodeUseCase in tests/unit/test_delete_node_use_case.py
- [X] T068 [US5] Implement DeleteNodeUseCase in src/linemark/use_cases/delete_node.py with interactive confirmation and --force flag

### CLI Implementation

- [X] T069 [US5] Implement `lmk delete` command in src/linemark/cli/main.py with -r, -p, --force, --directory options

### Integration Test

- [X] T070 [US5] Write integration test in tests/integration/test_delete_workflow.py verifying recursive and promote deletion modes

**Story 5 Validation**: Run integration test. User should be able to delete nodes with different strategies.

---

## Phase 8: User Story 6 - Restore Numbering (P4)

**Story Goal**: Writers can restore clean, evenly-spaced numbering after many insertions.

**Independent Test Criteria**:
- ✅ User creates outline with irregular spacing (001, 003, 007, etc.)
- ✅ User runs `lmk compact`
- ✅ Siblings renumbered with 100-unit spacing (001, 100, 200)
- ✅ Hierarchy preserved, all files renamed correctly

### Use Case Implementation

- [X] T071 [P] [US6] Write unit test for CompactOutlineUseCase in tests/unit/test_compact_outline_use_case.py
- [X] T072 [US6] Implement CompactOutlineUseCase in src/linemark/use_cases/compact_outline.py using tiered redistribution algorithm per research.md R3

### CLI Implementation

- [X] T073 [US6] Implement `lmk compact` command in src/linemark/cli/main.py with optional SQID/MP for subtree compaction

### Integration Test

- [X] T074 [US6] Write integration test in tests/integration/test_compact_workflow.py verifying multi-level compaction

**Story 6 Validation**: Run integration test. User should be able to compact outline and see ideal spacing restored.

---

## Phase 9: User Story 7 - Validate and Repair Integrity (P4)

**Story Goal**: Users can detect and fix structural problems (duplicate identifiers, invalid naming, etc.).

**Independent Test Criteria**:
- ✅ User manually creates invalid state (duplicate SQIDs, missing files)
- ✅ User runs `lmk doctor`
- ✅ Issues detected and reported or auto-repaired
- ✅ Outline passes validation after doctor completes

### Use Case Implementation

- [X] T075 [P] [US7] Write unit test for ValidateOutlineUseCase in tests/unit/test_validate_outline_use_case.py
- [X] T076 [US7] Implement ValidateOutlineUseCase in src/linemark/use_cases/validate_outline.py checking invariants per Outline.validate_invariants() and auto-repairing issues

### CLI Implementation

- [X] T077 [US7] Implement `lmk doctor` command in src/linemark/cli/main.py with repair logic and summary output

### Integration Test

- [X] T078 [US7] Write integration test in tests/integration/test_doctor_workflow.py verifying detection and repair of duplicate SQIDs, missing types, invalid paths

**Story 7 Validation**: Run integration test. User should be able to run doctor and see outline repaired.

---

## Phase 10: User Story 8 - View Different Formats (P4)

**Story Goal**: Users can view outline as visual tree or structured JSON for integration.

**Independent Test Criteria**:
- ✅ User runs `lmk list` and sees human-readable tree with indentation
- ✅ User runs `lmk list --json` and gets valid nested JSON with children arrays
- ✅ Both formats show complete hierarchy

### Implementation

- [X] T079 [P] [US8] Implement JSON formatter in src/linemark/cli/formatters.py generating nested structure with children arrays
- [X] T080 [US8] Update ListOutlineUseCase in src/linemark/use_cases/list_outline.py to support JSON format flag
- [X] T081 [US8] Update `lmk list` command in src/linemark/cli/main.py to use --json flag

### Integration Test

- [X] T082 [US8] Write integration test in tests/integration/test_list_formats.py verifying tree and JSON output correctness

**Story 8 Validation**: Run integration test. User should see both output formats working.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Goal**: Ensure production readiness with error handling, documentation, and quality gates.

### Error Handling

- [X] T083 [P] Implement domain exceptions in src/linemark/domain/exceptions.py (MaterializedPathExhaustedError, DuplicateSQIDError, etc.)
- [X] T084 [P] Add fail-fast error handling to all use cases per FR-042 (descriptive messages, no retries)
- [X] T085 [P] Add error handling to CLI commands with stderr output and appropriate exit codes

### Entry Points & Packaging

- [X] T086 [P] Implement __main__.py in src/linemark/__main__.py for `python -m linemark` execution
- [X] T087 [P] Add console script entry point in pyproject.toml for `lmk` command
- [X] T088 [P] Create _version.py in src/linemark/_version.py with version string

### Quality Gates

- [X] T089 Run pytest with 90% coverage: `pytest --cov=src/linemark --cov-report=term-missing` (207 tests pass, 90% coverage)
- [X] T090 Run mypy in strict mode: `mypy src/linemark --strict` (PASS)
- [X] T091 Run ruff linting: `ruff check src/ tests/` (PASS)
- [X] T092 Fix any quality gate violations until all pass with zero warnings (PASS)

**Final Validation**: All quality gates pass (100% coverage, mypy strict, ruff clean).

---

## Dependency Graph & Execution Order

### Story Dependencies

```
Setup (Phase 1)
    ↓
Foundational (Phase 2: Domain + Ports)
    ↓
    ├─→ User Story 1 (P1) [INDEPENDENT - Can start after Foundational]
    │
    ├─→ User Story 2 (P2) [DEPENDS on US1 for baseline functionality]
    │
    ├─→ User Story 3 (P2) [DEPENDS on US1 for baseline functionality]
    │
    ├─→ User Story 4 (P3) [DEPENDS on US1 for baseline functionality]
    │
    ├─→ User Story 5 (P3) [DEPENDS on US1 for baseline functionality]
    │
    ├─→ User Story 6 (P4) [DEPENDS on US1, US2 for move operations]
    │
    ├─→ User Story 7 (P4) [DEPENDS on US1-US5 for complete validation]
    │
    └─→ User Story 8 (P4) [DEPENDS on US1 for list functionality]

All Stories Complete
    ↓
Polish & Cross-Cutting (Phase 11)
```

### Critical Path

1. **Setup** (T001-T005) - BLOCKING
2. **Foundational** (T006-T023) - BLOCKING
3. **US1: Create Nodes** (T024-T041) - BLOCKING for all other stories
4. **US2-US8** can proceed in parallel after US1 completes
5. **Polish** (T083-T092) - Final phase

### Recommended MVP Scope

**MVP = User Story 1 Only** (T001-T041)

This delivers:
- ✅ Add nodes hierarchically
- ✅ List outline in tree format
- ✅ Complete TDD implementation
- ✅ All quality gates passing

**Estimated Effort**: ~40% of total tasks (41 of 92)

**Value**: Writers can immediately start organizing content with stable identifiers and hierarchy.

---

## Parallel Execution Examples

### Phase 2 (Foundational) Parallelization

After T007 (MaterializedPath basics) completes:

**Parallel Group 1** (can run simultaneously):
- T008-T009: MaterializedPath.parent()
- T010-T011: MaterializedPath.child()
- T012-T013: MaterializedPath validation
- T014-T015: SQID value object
- T016-T019: Node entity

**Parallel Group 2** (after Group 1):
- T021: FileSystemPort
- T022: SQIDGeneratorPort
- T023: SlugifierPort

### Phase 3 (User Story 1) Parallelization

After domain logic (T030-T032) completes:

**Parallel Group 1** (adapter implementations):
- T024-T025: FileSystemAdapter
- T026-T027: SQIDGeneratorAdapter
- T028-T029: SlugifierAdapter

**Parallel Group 2** (use cases - after adapters):
- T033-T034: AddNodeUseCase
- T035-T036: ListOutlineUseCase

### Phase 11 (Polish) Parallelization

**Parallel Group 1** (independent concerns):
- T083: Domain exceptions
- T084: Use case error handling
- T085: CLI error handling
- T086: __main__.py
- T087: Entry point
- T088: Version file

**Sequential Group 2** (after all implementation):
- T089 → T090 → T091 → T092: Quality gates (run sequentially to fix issues)

---

## Task Execution Guidelines

### Test-First Discipline (MANDATORY)

For EVERY implementation task:
1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass
3. **Refactor**: Clean up while keeping tests green

**Example Flow**:
```
T006 (Write test) → T007 (Implement)
    ↓ RED            ↓ GREEN
T008 (Write test) → T009 (Implement)
    ↓ RED            ↓ GREEN
```

### Quality Gate Checkpoints

Run quality gates after each phase:
- After Foundational: `pytest tests/unit/ --cov=src/linemark/domain --cov=src/linemark/ports`
- After each User Story: `pytest tests/integration/test_<story>_workflow.py`
- After Polish: All gates (coverage, mypy, ruff)

### File Path Verification

Each task specifies exact file paths. Verify:
- ✅ File created in correct location
- ✅ Imports work (`from src.linemark.domain import entities`)
- ✅ Tests can import implementation

---

## Implementation Notes

### Constitutional Compliance

- **Hexagonal Architecture**: Domain (T006-T020) → Ports (T021-T023) → Adapters (T024-T029) → Use Cases (T033+) → CLI (T037+)
- **Test-First**: Every implementation task has preceding test task
- **100% Coverage**: T089 enforces coverage requirement
- **Quality Gates**: T089-T092 enforce mypy strict and ruff clean
- **Plain Text**: All storage via markdown files (no database)

### Adapter Testing

Use **fake adapters** in unit tests, **real adapters** in integration tests:

```python
# Unit test (fast, isolated)
def test_add_node_use_case():
    fs = FakeFileSystem()  # In-memory fake
    use_case = AddNodeUseCase(filesystem=fs, ...)
    use_case.execute(...)
    assert "001_" in fs.files

# Integration test (slower, real filesystem)
def test_add_workflow(tmp_path):
    fs = FileSystemAdapter()  # Real adapter
    # Test with actual files in tmp_path
```

### SQID Counter Derivation

Per clarification decision (research.md R1):
- Counter derived by scanning existing files at startup
- Decode all SQIDs to integers, find max, use max+1

Implement in startup logic (T034 AddNodeUseCase initialization).

---

## Success Criteria

✅ **Phase 1-2 Complete**: Domain logic + ports tested at 100% coverage, zero dependencies
✅ **US1 Complete**: User can add nodes and list hierarchy (MVP achieved)
✅ **US2-8 Complete**: All user stories independently verified
✅ **Quality Gates Pass**: 100% coverage, mypy strict, ruff clean
✅ **Constitutional Compliance**: All 5 principles satisfied

**Final Deliverable**: Production-ready CLI tool for hierarchical markdown outline management.
