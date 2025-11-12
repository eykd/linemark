<!--
Sync Impact Report:
Version Change: [INITIAL] → 1.0.0
Constitution created from template with project-specific values.

Modified Principles: N/A (initial creation)
Added Sections: All sections populated from template
Removed Sections: None

Templates Updated:
✅ plan-template.md - Reviewed, constitution check section aligns
✅ spec-template.md - Reviewed, requirements align with principles
✅ tasks-template.md - Reviewed, test-first discipline reflected

Follow-up TODOs: None
-->

# Linemark Constitution

## Core Principles

### I. Hexagonal Architecture (Ports & Adapters)

Every feature MUST follow hexagonal architecture with clear separation of concerns:
- **Domain**: Pure business logic with no external dependencies
- **Ports**: Protocols/interfaces defining contracts for external interactions
- **Adapters**: Concrete implementations of ports (file system, CLI, etc.)
- **Use Cases**: Application logic orchestrating domain and ports
- **CLI**: Thin command-line interface layer

**Rationale**: This architecture ensures core logic remains independent of frameworks, file systems, and external dependencies, enabling easier testing, flexibility, and long-term maintainability.

### II. Test-First Development (NON-NEGOTIABLE)

TDD is MANDATORY for all code:
- Tests MUST be written before implementation
- Tests MUST fail before implementation begins
- Red-Green-Refactor cycle MUST be strictly followed
- User approval of tests MUST be obtained before implementation
- Tests include: contract tests (ports/protocols), unit tests (domain logic), integration tests (complete workflows)

**Rationale**: Test-first ensures code is testable by design, requirements are clear before coding, and regression protection is built-in from the start.

### III. 100% Quality Gates (NON-NEGOTIABLE)

All code MUST pass these gates before commit:
- **100% test coverage**: All code paths covered by tests
- **100% mypy strict mode**: Complete type safety with no type: ignore
- **100% ruff linting**: No linting violations (extensive ruleset enabled)
- No warnings, no exceptions, no compromises

**Rationale**: Zero tolerance for quality gaps prevents technical debt accumulation, ensures consistency across the codebase, and maintains professional standards.

### IV. Plain Text Storage

All data MUST be stored in plain text formats:
- Markdown for content and structure
- YAML frontmatter for metadata
- Git-friendly, diff-friendly formats
- Human-readable and editor-agnostic
- Compatible with tools like Obsidian, static site generators

**Rationale**: Plain text ensures data longevity, tool independence, version control compatibility, and user ownership of content without proprietary lock-in.

### V. CLI-First Interface

All functionality MUST be accessible via command-line interface:
- Text in (stdin/args) → text out (stdout)
- Errors to stderr with appropriate exit codes
- Support both human-readable and machine-parsable formats
- Integration with standard Unix tooling and pipelines

**Rationale**: CLI-first design enables scripting, automation, integration with other tools, and serves as foundation for potential future UIs.

## Development Workflow

### Test Organization

Tests MUST be organized by type with clear purposes:
- **Contract tests** (`tests/contract/`): Verify ports/protocols/interfaces are correctly defined
- **Unit tests** (`tests/unit/`): Test individual domain components in isolation
- **Integration tests** (`tests/integration/`): Test complete workflows end-to-end

### Dependency Injection

Use container-based dependency injection:
- Containers group related dependencies (e.g., TemplatesContainer)
- Ports injected as constructor parameters
- Facilitates testing with fake adapters
- Explicit dependencies, no hidden coupling

### File-Based Repository Pattern

For data persistence:
- Repository ports define abstract operations (save, load, list, etc.)
- File-based adapters implement concrete storage
- Domain entities remain storage-agnostic
- Atomic operations with transactional safety where needed

## Technology Standards

### Required Stack

- **Language**: Python 3.13+
- **CLI Framework**: Click 8.1.8+ or Typer 0.12.0+
- **Storage**: PyYAML 6.0.2+ (YAML frontmatter)
- **Validation**: Pydantic 2.11.4+
- **Testing**: pytest 8.3.5+ with pytest-cov, pytest-mock
- **Type Checking**: mypy 1.15.0+ (strict mode)
- **Linting**: ruff 0.11.8+ (comprehensive ruleset)
- **Identifiers**: UUIDv7 (temporal ordering with collision resistance)

### Code Quality Configuration

**ruff** configuration MUST include:
- All standard rulesets (A, ANN, ARG, B, C, D, E, F, etc.)
- Strict docstring requirements (pydocstyle D)
- Type annotation enforcement (flake8-annotations ANN)
- Security checks (flake8-bandit S)
- Per-file ignores only for tests and interfaces where justified

**mypy** MUST run in strict mode:
- No implicit Optional
- No untyped definitions
- No implicit reexport
- Pydantic plugin enabled

**pytest** MUST enforce:
- Coverage reporting with no-cov-on-fail
- Random test order (pytest-random-order)
- Strict markers and config

## Governance

### Constitution Supremacy

This constitution supersedes all other practices, guidelines, and preferences. When conflicts arise, the constitution takes precedence.

### Amendment Process

Amendments require:
1. **Documentation**: Proposed changes with rationale
2. **Version Bump**: Semantic versioning (MAJOR.MINOR.PATCH)
   - MAJOR: Backward incompatible changes (principle removal/redefinition)
   - MINOR: New principles or materially expanded guidance
   - PATCH: Clarifications, wording fixes, non-semantic refinements
3. **Impact Analysis**: Review all dependent templates and documentation
4. **Approval**: Explicit acceptance of constitutional change
5. **Migration Plan**: For breaking changes requiring code updates

### Compliance Verification

All pull requests and reviews MUST verify:
- Architecture follows hexagonal pattern
- Tests written before implementation
- 100% coverage, mypy, ruff compliance achieved
- Plain text storage used for all data
- CLI interface properly implemented

### Complexity Justification

Any introduction of complexity beyond these principles MUST be:
- **Documented**: Why the complexity is necessary
- **Justified**: What simpler alternative was rejected and why
- **Approved**: Explicit sign-off on the complexity addition
- **Minimal**: Smallest viable addition to solve the problem

Use `CLAUDE.md` for project-specific context and feature tracking. This file provides runtime development guidance without modifying constitutional principles.

**Version**: 1.0.0 | **Ratified**: 2025-11-12 | **Last Amended**: 2025-11-12
