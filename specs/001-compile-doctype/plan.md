# Implementation Plan: Compile Doctype Command

**Branch**: `001-compile-doctype` | **Date**: 2025-11-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-compile-doctype/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add a new `lmk compile <doctype> [optional-SQID]` command that concatenates all content for a specified doctype (e.g., "draft", "notes") from the entire forest or a specific subtree. The command traverses nodes in depth-first order (lexicographical by materialized path), outputs to stdout with configurable separators (default: '\n\n---\n\n'), and supports escape sequence interpretation for separators. Empty/whitespace-only files are skipped, and the command validates that the doctype exists before compilation.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Click 8.1.8+ (CLI framework), PyYAML 6.0.2+ (frontmatter), python-slugify 8.0.0+ (slugs), sqids 0.5.0+ (identifiers), Pydantic 2.11.4+ (validation)
**Storage**: Filesystem (flat directory with .md files using YAML frontmatter metadata)
**Testing**: pytest 8.3.5+ with pytest-cov, pytest-mock, 100% coverage requirement
**Target Platform**: Cross-platform CLI (Linux, macOS, Windows)
**Project Type**: Single project (CLI tool with hexagonal architecture)
**Performance Goals**: Responsive for typical forests (< 10,000 nodes), compile in under 5 seconds for 1,000 documents
**Constraints**: Must support large text files (up to 10MB per doctype file), maintain low memory footprint (stream if needed), UTF-8 encoding by default
**Scale/Scope**: Handle forests with up to 10,000 nodes and multiple doctypes per node (draft, notes, summary, etc.)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Hexagonal Architecture** | ✅ PASS | Command will follow existing pattern: CLI layer → Use Case → Domain logic with FileSystem port |
| **II. Test-First Development** | ✅ PASS | Will follow TDD with contract/unit/integration tests before implementation |
| **III. 100% Quality Gates** | ✅ PASS | 100% test coverage, mypy strict mode, ruff linting - no exceptions |
| **IV. Plain Text Storage** | ✅ PASS | Uses existing markdown files with YAML frontmatter (no new storage format) |
| **V. CLI-First Interface** | ✅ PASS | New `lmk compile` command with text in/out, stderr for errors |

**Pre-Phase 0 Evaluation**: All gates PASS. No constitutional violations. Feature fits naturally into existing architecture.

**Post-Phase 1 Re-Evaluation** (after design complete):

| Principle | Status | Evidence |
|-----------|--------|----------|
| **I. Hexagonal Architecture** | ✅ PASS | Design confirms: Use case in application layer, FileSystem port for I/O, CLI thin adapter |
| **II. Test-First Development** | ✅ PASS | Quickstart outlines TDD workflow: contract → unit → integration tests before implementation |
| **III. 100% Quality Gates** | ✅ PASS | Quality checklist in quickstart enforces 100% coverage, mypy strict, ruff linting |
| **IV. Plain Text Storage** | ✅ PASS | Design uses existing .md files with YAML frontmatter, no new storage formats |
| **V. CLI-First Interface** | ✅ PASS | CLI contract defines text in/out, proper exit codes, shell-friendly design |

**Final Evaluation**: All constitutional principles satisfied. Design is approved for implementation.

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
├── domain/
│   ├── entities.py           # Node, MaterializedPath (existing)
│   └── exceptions.py          # Custom exceptions (existing)
├── ports/
│   └── filesystem.py          # FileSystem protocol (existing)
├── adapters/
│   └── filesystem.py          # FileSystemAdapter (existing)
├── use_cases/
│   └── compile_doctype.py     # NEW: CompileDoctypeUseCase
└── cli/
    └── main.py                # NEW: compile command added

tests/
├── contract/
│   └── test_compile_doctype_contract.py  # NEW: Port contracts
├── unit/
│   └── test_compile_doctype_unit.py      # NEW: Use case logic
└── integration/
    └── test_compile_doctype_integration.py  # NEW: E2E workflows
```

**Structure Decision**: Single project following existing hexagonal architecture. New functionality adds:
1. `CompileDoctypeUseCase` in `use_cases/` - orchestrates compilation logic
2. `compile` command in `cli/main.py` - CLI entry point
3. Leverages existing `FileSystemAdapter` and `FileSystem` port
4. Comprehensive test coverage across all three test layers

## Complexity Tracking

**No violations**: All constitutional principles satisfied. No additional complexity introduced beyond standard hexagonal architecture pattern already in use.
