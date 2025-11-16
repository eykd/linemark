# Implementation Plan: Node and Document Type Operations

**Branch**: `001-node-doctype-commands` | **Date**: 2025-11-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-node-doctype-commands/spec.md`

## Summary

Add three new CLI commands to the linemark tool for working with individual nodes and document types:
- `lmk types read` - Read document type content for a specific node
- `lmk types write` - Write document type content from stdin
- `lmk search` - Search across nodes for regex/literal patterns

These commands enable direct manipulation of document type files and powerful search capabilities across the outline, supporting automation and scripting workflows.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Click 8.1.8+ (CLI), PyYAML 6.0.2+ (frontmatter), sqids 0.5.0+ (identifiers), Python `re` module (regex)
**Storage**: Filesystem (markdown files with YAML frontmatter in flat directory)
**Testing**: pytest 8.3.5+ with pytest-cov, pytest-mock
**Target Platform**: Linux/macOS/Windows CLI
**Project Type**: Single (existing linemark CLI application)
**Performance Goals**: Read <2s, Write <3s, Search 1000+ nodes <5s
**Constraints**: Atomic writes (temp-then-rename), YAML frontmatter preservation, outline position ordering
**Scale/Scope**: Support 1000+ nodes, handle MB+ document bodies

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Hexagonal Architecture
- ✅ **Domain**: Search logic, file path resolution, SQID validation (pure business logic)
- ✅ **Ports**: FileSystemPort (already exists), add ReadTypePort, WriteTypePort, SearchPort protocols
- ✅ **Adapters**: Extend FileSystemAdapter for atomic writes, create SearchAdapter for regex matching
- ✅ **Use Cases**: ReadTypeUseCase, WriteTypeUseCase, SearchUseCase orchestrating domain + ports
- ✅ **CLI**: Three new commands in cli/main.py (thin layer invoking use cases)

### Test-First Development (NON-NEGOTIABLE)
- ✅ Tests MUST be written before implementation
- ✅ Red-Green-Refactor cycle strictly followed
- ✅ User approval of tests before implementation begins
- ✅ Test types: contract tests (ports), unit tests (use cases), integration tests (CLI workflows)

### 100% Quality Gates (NON-NEGOTIABLE)
- ✅ 100% test coverage required
- ✅ 100% mypy strict mode (no type: ignore)
- ✅ 100% ruff linting (all rules enabled per pyproject.toml)
- ✅ No warnings, no exceptions

### Plain Text Storage
- ✅ Markdown files with YAML frontmatter (existing format)
- ✅ Git-friendly, diff-friendly
- ✅ Human-readable and editor-agnostic

### CLI-First Interface
- ✅ stdin → stdout paradigm (especially for `types write` and `types read`)
- ✅ Errors to stderr with appropriate exit codes
- ✅ Support JSON output format (`--json` for search)
- ✅ Unix pipeline compatible

**Gate Status**: ✅ PASS - All constitutional principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/001-node-doctype-commands/
├── plan.md              # This file
├── research.md          # Phase 0 output (technical research)
├── data-model.md        # Phase 1 output (entities and file structure)
├── quickstart.md        # Phase 1 output (user guide)
├── contracts/           # Phase 1 output (port protocols)
│   ├── read_type_port.py
│   ├── write_type_port.py
│   └── search_port.py
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/linemark/
├── domain/
│   ├── entities.py                # Existing (Node, etc.)
│   ├── exceptions.py              # Add SearchError, InvalidRegexError
│   └── search.py                  # NEW: Search domain logic
├── ports/
│   ├── filesystem.py              # Existing FileSystemPort
│   ├── read_type.py               # NEW: ReadTypePort protocol
│   ├── write_type.py              # NEW: WriteTypePort protocol
│   └── search.py                  # NEW: SearchPort protocol
├── adapters/
│   ├── filesystem.py              # Extend with atomic write support
│   ├── read_type_adapter.py       # NEW: Implements ReadTypePort
│   ├── write_type_adapter.py      # NEW: Implements WriteTypePort (atomic)
│   └── search_adapter.py          # NEW: Implements SearchPort (regex)
├── use_cases/
│   ├── read_type.py               # NEW: ReadTypeUseCase
│   ├── write_type.py              # NEW: WriteTypeUseCase
│   └── search.py                  # NEW: SearchUseCase
└── cli/
    └── main.py                    # Add three new commands

tests/
├── contract/
│   ├── test_read_type_port.py     # NEW: ReadTypePort contract
│   ├── test_write_type_port.py    # NEW: WriteTypePort contract
│   ├── test_search_port.py        # NEW: SearchPort contract
│   ├── test_read_type_adapter.py  # NEW: ReadTypeAdapter implementation
│   ├── test_write_type_adapter.py # NEW: WriteTypeAdapter implementation
│   └── test_search_adapter.py     # NEW: SearchAdapter implementation
├── unit/
│   ├── test_read_type_use_case.py # NEW: ReadTypeUseCase logic
│   ├── test_write_type_use_case.py # NEW: WriteTypeUseCase logic
│   ├── test_search_use_case.py    # NEW: SearchUseCase logic
│   └── test_search_domain.py      # NEW: Search domain logic
└── integration/
    ├── test_types_read_workflow.py # NEW: End-to-end read command
    ├── test_types_write_workflow.py # NEW: End-to-end write command
    └── test_search_workflow.py    # NEW: End-to-end search command
```

**Structure Decision**: Single project structure (Option 1) - this is an enhancement to the existing linemark CLI application, not a new project. All code follows the established hexagonal architecture pattern with domain, ports, adapters, use cases, and CLI layers.

## Complexity Tracking

> **No constitutional violations requiring justification**

All aspects of this feature align with constitutional principles:
- Hexagonal architecture maintained
- Test-first development enforced
- 100% quality gates required
- Plain text storage used
- CLI-first interface preserved
