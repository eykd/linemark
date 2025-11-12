# Implementation Plan: Linemark - Hierarchical Markdown Outline Manager

**Branch**: `001-linemark-cli-mvp` | **Date**: 2025-11-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/workspace/specs/001-linemark-cli-mvp/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Linemark is a command-line tool that manages hierarchical outlines of Markdown documents using filename-based organization. It encodes hierarchy in materialized paths (three-digit segments like `001-100-050`), assigns stable unique identifiers (SQIDs) to nodes, and supports multiple document types per node (draft, notes, custom types). The tool operates on flat directories with no external database, making outlines git-friendly and tool-agnostic.

**Technical Approach**: Hexagonal architecture with domain logic for outline management, file system adapter for storage, CLI adapter for user interaction, and SQID generation using the sqids library. All state derives from scanning existing files at startup (stateless, self-healing design).

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Click 8.1.8+ (CLI), sqids 0.5.0+ (identifiers), PyYAML 6.0.2+ (frontmatter), python-slugify 8.0.0+ (title slugs), Pydantic 2.11.4+ (validation)
**Storage**: Filesystem (flat directory with .md files), YAML frontmatter for metadata
**Testing**: pytest 8.3.5+ with pytest-cov, pytest-mock
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single CLI application
**Performance Goals**: <5s node creation, <2s list 100 nodes, <10s move subtree with 50+ files (per SC-001, SC-002, SC-003)
**Constraints**: No external database, no config files (MVP), flat directory only, 3-digit path segments (001-999)
**Scale/Scope**: Support 1,000+ nodes without degradation, depth ≥5 levels (per SC-004, FR-037)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Hexagonal Architecture ✅

**Status**: PASS

- **Domain**: Outline management logic (node creation, hierarchy manipulation, path calculation) with zero dependencies
- **Ports**: FileSystemPort (read/write files), SQIDGeneratorPort (identifier creation), SlugifierPort (title normalization)
- **Adapters**: FileSystemAdapter (pathlib-based), SQIDAdapter (sqids library), SlugAdapter (python-slugify)
- **Use Cases**: AddNode, MoveNode, DeleteNode, RenameNode, CompactOutline, ValidateOutline, ListOutline, ManageTypes
- **CLI**: Click-based command layer delegating to use cases

**Rationale**: Clean separation allows testing domain logic without filesystem, swapping storage implementations, and future GUI/API frontends.

### II. Test-First Development ✅

**Status**: PASS (Commitment Required)

- TDD will be strictly followed for all implementation
- Contract tests verify port interfaces
- Unit tests cover domain logic (path calculations, hierarchy rules, SQID generation)
- Integration tests validate complete workflows (add→move→delete→doctor)
- User approval required before implementation proceeds

**Rationale**: Critical for filesystem operations that could corrupt user data.

### III. 100% Quality Gates ✅

**Status**: PASS (Commitment Required)

- 100% test coverage enforced via pytest-cov
- mypy strict mode for type safety (Pydantic models, ports, adapters)
- ruff with comprehensive ruleset (including docstrings, type annotations, security)
- No exceptions, no warnings

**Rationale**: CLI tool must be rock-solid - users trust it with their writing projects.

### IV. Plain Text Storage ✅

**Status**: PASS

- All data in .md files with YAML frontmatter (title in draft files)
- Hierarchy encoded in filenames (materialized paths + SQIDs)
- No database, no binary formats
- Git-friendly, diff-friendly, Obsidian-compatible

**Rationale**: Aligns perfectly with spec requirement "filenames as source of truth" and Obsidian compatibility (SC-008).

### V. CLI-First Interface ✅

**Status**: PASS

- All commands via CLI: `lmk add`, `lmk move`, `lmk delete`, `lmk list`, etc.
- Human-readable tree output (default) and JSON output (--json flag)
- Errors to stderr with descriptive messages, success to stdout
- Exit codes for scripting (0=success, non-zero=error)

**Rationale**: Matches spec requirements exactly (FR-021, FR-022, FR-042).

### Overall Assessment

**GATE STATUS**: ✅ **PASS** - All constitutional principles aligned with feature requirements. No violations or complexity justifications needed.

### Post-Design Re-evaluation (Phase 1 Complete)

**Status**: ✅ **CONFIRMED PASS**

Design artifacts confirm constitutional alignment:

- **Research (R1-R8)**: All technology choices align with constitution requirements (sqids, Click, PyYAML, pytest, mypy, ruff)
- **Data Model**: Pure Pydantic models for domain (hexagonal architecture maintained)
- **Contracts**: Protocol-based ports enable testing without implementations (TDD-friendly)
- **Quickstart**: Explicit TDD workflow with quality gates (100% coverage, mypy strict, ruff clean)

No design changes needed. Ready for task generation (`/speckit.tasks`).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/linemark/
├── __init__.py
├── __main__.py              # Entry point for python -m linemark
├── domain/                  # Pure business logic (no dependencies)
│   ├── __init__.py
│   ├── entities.py          # Node, MaterializedPath, SQID value objects
│   ├── outline.py           # Outline aggregate root
│   └── exceptions.py        # Domain-specific errors
├── ports/                   # Interfaces for external dependencies
│   ├── __init__.py
│   ├── filesystem.py        # FileSystemPort protocol
│   ├── sqid_generator.py   # SQIDGeneratorPort protocol
│   └── slugifier.py         # SlugifierPort protocol
├── adapters/                # Concrete implementations of ports
│   ├── __init__.py
│   ├── filesystem.py        # PathLib-based file operations
│   ├── sqid_generator.py   # sqids library wrapper
│   └── slugifier.py         # python-slugify wrapper
├── use_cases/               # Application logic orchestrating domain + ports
│   ├── __init__.py
│   ├── add_node.py
│   ├── move_node.py
│   ├── delete_node.py
│   ├── rename_node.py
│   ├── list_outline.py
│   ├── compact_outline.py
│   ├── validate_outline.py  # "doctor" command
│   └── manage_types.py
├── cli/                     # Click-based command interface
│   ├── __init__.py
│   ├── main.py              # Click group and command definitions
│   └── formatters.py        # Tree/JSON output formatting
└── _version.py              # Version string

tests/
├── contract/                # Port interface verification
│   ├── __init__.py
│   ├── test_filesystem_port.py
│   ├── test_sqid_generator_port.py
│   └── test_slugifier_port.py
├── unit/                    # Domain logic in isolation
│   ├── __init__.py
│   ├── test_entities.py
│   ├── test_outline.py
│   ├── test_materialized_path.py
│   └── test_use_cases.py
└── integration/             # End-to-end workflows
    ├── __init__.py
    ├── test_add_workflow.py
    ├── test_move_workflow.py
    ├── test_delete_workflow.py
    ├── test_compact_workflow.py
    └── test_doctor_workflow.py
```

**Structure Decision**: Single CLI application using hexagonal architecture. Domain layer contains pure Python logic for outline management, hierarchy calculations, and validation rules. Ports define abstract interfaces for filesystem, SQID generation, and slug creation. Adapters provide concrete implementations. Use cases orchestrate domain logic and ports. CLI layer is a thin wrapper around use cases using Click framework.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - All constitutional principles are satisfied without exceptions.
