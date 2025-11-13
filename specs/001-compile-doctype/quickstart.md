# Quickstart: Implementing Compile Doctype Command

**Feature**: `001-compile-doctype`
**Date**: 2025-11-13
**Estimated Time**: 4-6 hours (following TDD)

## Prerequisites

- Development environment set up with Python 3.13+
- All dependencies installed (`uv sync`)
- Familiar with existing codebase structure
- Understanding of hexagonal architecture pattern

## Implementation Roadmap

### Phase 1: Contract Tests (30-45 min)

Define behavior before implementation.

**Files to create**:
- `tests/contract/test_compile_doctype_contract.py`

**Key test cases**:
1. Use case constructor accepts FileSystem port
2. Execute method signature and return type
3. Basic error conditions (doctype not found, invalid SQID)
4. Empty result handling

**Run**: Tests MUST fail (red phase)
```bash
uv run pytest tests/contract/test_compile_doctype_contract.py -v
```

### Phase 2: Domain Exception (15 min)

Add the new exception type.

**File to modify**:
- `src/linemark/domain/exceptions.py`

**Add**:
```python
class DoctypeNotFoundError(DomainException):
    """Raised when doctype not found in forest/subtree."""

    def __init__(self, doctype: str, sqid: str | None = None) -> None:
        scope = f"subtree @{sqid}" if sqid else "forest"
        super().__init__(
            f"Doctype '{doctype}' not found in {scope}. "
            f"Check doctype name and ensure at least one node has this file."
        )
        self.doctype = doctype
        self.sqid = sqid
```

### Phase 3: Use Case Implementation (90-120 min)

Implement core business logic following TDD.

**File to create**:
- `src/linemark/use_cases/compile_doctype.py`

**Implementation steps**:
1. Create minimal `CompileDoctypeUseCase` class (make contract tests pass)
2. Write unit test for node collection logic
3. Implement node collection (list outline + optional filtering)
4. Write unit test for doctype validation
5. Implement doctype validation (scan for existence)
6. Write unit test for content collection
7. Implement content collection (read files, skip empty)
8. Write unit test for separator handling
9. Implement separator processing (escape sequences)
10. Write unit test for output generation
11. Implement output concatenation

**File to create**:
- `tests/unit/test_compile_doctype_unit.py`

**Run after each step**:
```bash
uv run pytest tests/unit/test_compile_doctype_unit.py -v
```

**Key implementation considerations**:
- Use existing FileSystem port methods
- Handle UTF-8 encoding errors gracefully
- Skip empty/whitespace-only files
- Maintain lexicographical ordering from list_outline

### Phase 4: CLI Command (30-45 min)

Add command-line interface.

**File to modify**:
- `src/linemark/cli/main.py`

**Add command**:
```python
@lmk.command()
@click.argument('doctype')
@click.argument('sqid', required=False)
@click.option(
    '--separator',
    default='\n\n---\n\n',
    help='Separator between documents (escape sequences interpreted)'
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)'
)
def compile(
    doctype: str,
    sqid: str | None,
    separator: str,
    directory: Path,
) -> None:
    """Compile all doctype files into a single document.

    ... (docstring content)
    """
    try:
        # Strip @ prefix if provided
        clean_sqid = sqid.lstrip('@') if sqid else None

        # Create adapters
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = CompileDoctypeUseCase(filesystem=filesystem)
        result = use_case.execute(
            doctype=doctype,
            directory=directory,
            sqid=clean_sqid,
            separator=separator,
        )

        # Output to stdout
        if result:
            click.echo(result, nl=False)

    except DoctypeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except NodeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(2)
```

**Update imports**:
```python
from linemark.use_cases.compile_doctype import CompileDoctypeUseCase
from linemark.domain.exceptions import DoctypeNotFoundError
```

### Phase 5: Integration Tests (60-90 min)

Test complete workflows end-to-end.

**File to create**:
- `tests/integration/test_compile_doctype_integration.py`

**Key test scenarios**:
1. Compile entire forest with multiple nodes
2. Compile specific subtree
3. Custom separator handling
4. Empty files skipped correctly
5. Escape sequence interpretation
6. Doctype not found error
7. SQID not found error
8. Empty result handling
9. Various node orderings

**Setup requirements**:
- Create temporary forest structures
- Populate with test doctype files
- Verify actual CLI command execution

**Run**:
```bash
uv run pytest tests/integration/test_compile_doctype_integration.py -v
```

### Phase 6: Quality Gates (30-45 min)

Ensure 100% compliance with quality standards.

**Run full test suite**:
```bash
uv run pytest tests/ -v --cov
```

**Check coverage**:
```bash
uv run pytest tests/ --cov --cov-report=html
open htmlcov/index.html
```

**Verify 100% coverage** - if not, add missing test cases.

**Run type checking**:
```bash
uv run mypy src/
```

**Fix any type errors** - MUST pass strict mode with no errors.

**Run linting**:
```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

**Fix any linting issues** - MUST have zero violations.

### Phase 7: Manual Testing (15-30 min)

Verify real-world usage.

**Test cases**:
```bash
# 1. Basic compilation
lmk compile draft

# 2. Subtree compilation (use real SQID from your forest)
lmk compile draft @YourSQID

# 3. Custom separator
lmk compile draft --separator "===PAGE BREAK==="

# 4. Escape sequences
lmk compile draft --separator "\n\n***\n\n"

# 5. Output to file
lmk compile draft > compiled_draft.md
cat compiled_draft.md

# 6. Error handling - invalid doctype
lmk compile nonexistent

# 7. Error handling - invalid SQID
lmk compile draft @invalid

# 8. Help text
lmk compile --help
```

## Development Tips

### TDD Workflow

1. **Write test** - Define expected behavior
2. **Run test** - Verify it fails (red)
3. **Write code** - Minimal implementation to pass
4. **Run test** - Verify it passes (green)
5. **Refactor** - Improve code quality
6. **Repeat** - Next test case

### Debugging Strategies

**Use pytest verbosity**:
```bash
uv run pytest -vv -s tests/unit/test_compile_doctype_unit.py::TestCompileDoctypeUseCase::test_specific_case
```

**Use pdb debugger**:
```python
import pdb; pdb.set_trace()
```

**Check file operations**:
```python
# In tests, use tmp_path fixture
def test_something(tmp_path):
    forest_dir = tmp_path / "forest"
    forest_dir.mkdir()
    # ... create test files

    # Print directory contents for debugging
    print(list(forest_dir.rglob("*.md")))
```

### Common Pitfalls

1. **Forgetting to strip @ prefix from SQID** - Handle in CLI layer
2. **Not handling UTF-8 decode errors** - Add graceful fallback
3. **Including separators incorrectly** - Between items only, not before/after
4. **Not skipping whitespace-only files** - Use `.isspace()` check
5. **Escape sequences not interpreted** - Use `codecs.decode('unicode_escape')`
6. **Breaking existing tests** - Run full suite regularly

### Quality Checklist

Before considering feature complete:
- [ ] All contract tests pass
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] 100% test coverage achieved
- [ ] mypy strict mode passes (zero errors)
- [ ] ruff linting passes (zero violations)
- [ ] Manual testing completed successfully
- [ ] Help text is clear and accurate
- [ ] Error messages are user-friendly
- [ ] Code follows existing patterns
- [ ] No TODOs or FIXMEs remaining

## Time Estimates

| Phase | Estimated Time | Notes |
|-------|----------------|-------|
| Contract Tests | 30-45 min | Define interfaces first |
| Domain Exception | 15 min | Simple addition |
| Use Case (TDD) | 90-120 min | Core logic, multiple test cycles |
| CLI Command | 30-45 min | Straightforward Click command |
| Integration Tests | 60-90 min | Comprehensive scenarios |
| Quality Gates | 30-45 min | Coverage, types, linting |
| Manual Testing | 15-30 min | Real-world verification |
| **Total** | **4-6 hours** | Assumes no major blockers |

**Note**: These are estimates for experienced developers familiar with the codebase. First-time feature implementation may take 1.5-2x longer.

## Success Criteria

Feature is complete when:
1. All tests pass (contract, unit, integration)
2. 100% test coverage achieved
3. mypy strict mode passes
4. ruff linting passes
5. Manual testing scenarios work correctly
6. CLI help text is accurate
7. Error messages are user-friendly
8. Code follows existing architectural patterns
9. No constitutional violations
10. Ready for code review

## Next Steps

After implementation complete:
1. Run `/speckit.tasks` to generate implementation task breakdown
2. Follow tasks.md for step-by-step implementation
3. Commit code following conventional commits
4. Create pull request
5. Address review feedback
6. Merge when approved

## Resources

- **Constitution**: `.specify/memory/constitution.md`
- **Spec**: `specs/001-compile-doctype/spec.md`
- **Research**: `specs/001-compile-doctype/research.md`
- **Data Model**: `specs/001-compile-doctype/data-model.md`
- **Contracts**: `specs/001-compile-doctype/contracts/`
- **This Guide**: `specs/001-compile-doctype/quickstart.md`
