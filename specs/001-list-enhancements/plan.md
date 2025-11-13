# Implementation Plan: Enhanced List Command with Subtree Filtering and Metadata Display

**Branch**: `001-list-enhancements` | **Date**: 2025-11-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-list-enhancements/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend the existing `lmk list` command to support three new capabilities: (1) optional SQID argument to display only a subtree, (2) `--show-doctypes` flag to display document types for each node, and (3) `--show-files` flag to show relative file paths. All enhancements must work with both tree text output and JSON output formats while maintaining existing behavior when no new options are used.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Click 8.1.8+, Pydantic 2.11.4+, PyYAML 6.0.2+, sqids 0.5.0+
**Storage**: Filesystem (markdown files with YAML frontmatter)
**Testing**: pytest 8.3.5+ with pytest-cov, pytest-mock
**Target Platform**: CLI tool (Linux, macOS, Windows)
**Project Type**: Single project (CLI application)
**Performance Goals**: Subtree filtering under 2 seconds, combined flags under 3 seconds for 100-node outlines
**Constraints**: Must maintain backward compatibility with existing `lmk list` command; tree text output must remain readable with metadata
**Scale/Scope**: Support outlines with 100+ nodes and up to 50 depth levels

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Check (Phase 0)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Hexagonal Architecture | ✅ PASS | Feature extends existing use case (`ListOutlineUseCase`); no new adapters required; formatters remain in presentation layer |
| II. Test-First Development | ✅ PASS | Will write tests before implementation per TDD workflow |
| III. 100% Quality Gates | ✅ PASS | All code will pass mypy strict, ruff, 100% coverage |
| IV. Plain Text Storage | ✅ PASS | No changes to storage format; reads existing markdown files |
| V. CLI-First Interface | ✅ PASS | Extends existing CLI command with optional args and flags |

**Verdict**: ✅ PROCEED TO PHASE 0

### Post-Design Check (Phase 1)

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Hexagonal Architecture | ✅ PASS | Design maintains clean separation: Use case handles filtering logic, formatters handle presentation, CLI orchestrates. No domain changes needed. |
| II. Test-First Development | ✅ PASS | Quickstart provides explicit TDD workflow with test cases defined before implementation. Red-Green-Refactor cycle documented. |
| III. 100% Quality Gates | ✅ PASS | Quality gates checklist included in quickstart. All code will be tested, type-checked, and linted. |
| IV. Plain Text Storage | ✅ PASS | No storage changes. Feature only reads existing markdown files. |
| V. CLI-First Interface | ✅ PASS | CLI contracts fully specified. Supports both human (tree) and machine (JSON) output. |

**Verdict**: ✅ ALL CHECKS PASSED - READY FOR IMPLEMENTATION

## Project Structure

### Documentation (this feature)

```text
specs/001-list-enhancements/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (to be created)
├── data-model.md        # Phase 1 output (to be created)
├── quickstart.md        # Phase 1 output (to be created)
├── contracts/           # Phase 1 output (to be created)
│   └── list_command.md  # CLI contract specification
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── linemark/
│   ├── use_cases/
│   │   └── list_outline.py        # MODIFY: Add subtree filtering, metadata enrichment
│   ├── cli/
│   │   ├── main.py                # MODIFY: Add SQID arg, --show-doctypes, --show-files flags
│   │   └── formatters.py          # MODIFY: Add metadata display to tree/JSON formatters
│   ├── domain/
│   │   └── entities.py            # NO CHANGES: Node already has all needed data
│   ├── ports/
│   │   └── filesystem.py          # NO CHANGES: Existing port sufficient
│   └── adapters/
│       └── filesystem.py          # NO CHANGES: Existing adapter sufficient

tests/
├── unit/
│   ├── test_list_outline_use_case.py      # MODIFY: Add subtree filtering tests
│   └── test_formatters.py                 # CREATE: Test metadata display in formatters
└── integration/
    └── test_list_command_integration.py   # CREATE: End-to-end tests for new features
```

**Structure Decision**: This is a single-project CLI application following the existing hexagonal architecture. Changes are isolated to:
- **Use Case Layer**: `list_outline.py` gains subtree filtering logic
- **CLI Layer**: `main.py` gets new optional arguments and flags
- **Presentation Layer**: `formatters.py` adds metadata display capabilities

No changes to domain entities or ports are needed since `Node` already contains `document_types` and file paths can be derived from existing data.

## Complexity Tracking

> **No violations identified**

All changes align with existing architecture patterns and constitutional principles. No complexity justification required.

