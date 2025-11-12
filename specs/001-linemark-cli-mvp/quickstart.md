# Quickstart: Building Linemark

**Feature**: Linemark - Hierarchical Markdown Outline Manager
**Date**: 2025-11-12
**Phase**: 1 (Design Complete)

## Overview

This guide provides a recommended implementation sequence for building Linemark following hexagonal architecture and test-first development (TDD) as mandated by the constitution.

**Key Principles**:
1. **Test-First**: Write failing tests before implementation
2. **Inside-Out**: Build domain → ports → adapters → use cases → CLI
3. **Red-Green-Refactor**: Fail → Pass → Clean
4. **100% Coverage**: All code paths tested

---

## Prerequisites

### Environment Setup

```bash
# Python 3.13+ required (constitution § Required Stack)
python --version  # Should be 3.13 or higher

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install \
    click>=8.1.8 \
    sqids>=0.5.0 \
    pyyaml>=6.0.2 \
    python-slugify>=8.0.0 \
    pydantic>=2.11.4 \
    pytest>=8.3.5 \
    pytest-cov \
    pytest-mock \
    mypy>=1.15.0 \
    ruff>=0.11.8
```

### Project Structure

```bash
# Create source structure (per plan.md)
mkdir -p src/linemark/{domain,ports,adapters,use_cases,cli}
mkdir -p tests/{contract,unit,integration}
touch src/linemark/__init__.py
touch src/linemark/__main__.py
```

---

## Implementation Sequence

### Phase 1: Domain Layer (Pure Logic, No Dependencies)

#### 1.1 Value Objects

**Test File**: `tests/unit/test_entities.py`

**TDD Steps**:

1. **Write test for MaterializedPath**:
```python
def test_materialized_path_from_string():
    mp = MaterializedPath.from_string("001-100-050")
    assert mp.segments == (1, 100, 50)
    assert mp.depth == 3
    assert mp.as_string == "001-100-050"
```

2. **Run test** (FAIL - MaterializedPath doesn't exist)
3. **Implement** `src/linemark/domain/entities.py` (MaterializedPath class)
4. **Run test** (PASS)
5. **Refactor** if needed

Repeat for:
- `MaterializedPath.parent()`
- `MaterializedPath.child(position)`
- Validation (segments 1-999)
- SQID value object
- DocumentType enum

**Success Criteria**: All value object tests pass, 100% coverage on entities.py

#### 1.2 Node Entity

**Test File**: `tests/unit/test_node.py`

**TDD Steps**:
1. Test node creation with required fields
2. Test `filename()` generation
3. Test `has_children()` and `get_children()` logic
4. Test `validate_required_types()`

**Success Criteria**: Node entity fully tested, immutability verified

#### 1.3 Outline Aggregate

**Test File**: `tests/unit/test_outline.py`

**TDD Steps**:
1. Test empty outline initialization
2. Test `get_by_sqid()` and `get_by_mp()`
3. Test `all_sorted()` lexicographic ordering
4. Test `validate_invariants()` catches duplicates
5. Test `find_next_sibling_position()` with tier spacing

**Success Criteria**: Outline aggregate passes all invariant tests

---

### Phase 2: Ports (Protocols Define Contracts)

**Test Files**: `tests/contract/test_*_port.py`

**TDD Steps**:

1. **Write contract test for FileSystemPort**:
```python
def test_filesystem_port_contract():
    # Verify protocol methods exist
    assert hasattr(FileSystemPort, 'read_file')
    assert hasattr(FileSystemPort, 'write_file')
    # ... etc
```

2. **Implement ports**: Copy port definitions from `specs/001-linemark-cli-mvp/contracts/` to `src/linemark/ports/`

3. **Run contract tests** (PASS - protocols defined correctly)

**Success Criteria**: All port protocols defined, contract tests pass

---

### Phase 3: Adapters (Concrete Implementations)

#### 3.1 FileSystemAdapter

**Test File**: `tests/contract/test_filesystem_adapter.py`

**TDD Steps**:

1. **Write adapter implementation test**:
```python
def test_filesystem_adapter_read_write(tmp_path):
    adapter = FileSystemAdapter()
    file = tmp_path / "test.md"

    adapter.write_file(file, "Hello")
    content = adapter.read_file(file)

    assert content == "Hello"
```

2. **Run test** (FAIL - FileSystemAdapter doesn't exist)
3. **Implement** `src/linemark/adapters/filesystem.py` using pathlib
4. **Run test** (PASS)

Repeat for all FileSystemPort methods.

**Success Criteria**: FileSystemAdapter passes all contract tests

#### 3.2 SQIDGeneratorAdapter

**Test File**: `tests/contract/test_sqid_adapter.py`

**TDD Steps**:
1. Test encode/decode round-trip
2. Test determinism (same input → same output)
3. Test invalid input handling

**Implementation**: Wrap sqids library in adapter

#### 3.3 SlugifierAdapter

**Test File**: `tests/contract/test_slugifier_adapter.py`

**TDD Steps**:
1. Test basic slugification
2. Test unicode handling
3. Test special character removal

**Implementation**: Wrap python-slugify in adapter

---

### Phase 4: Use Cases (Application Logic)

#### 4.1 AddNode Use Case

**Test File**: `tests/unit/test_add_node_use_case.py`

**TDD Steps**:

1. **Write use case test with fake adapters**:
```python
class FakeFileSystem:
    def __init__(self):
        self.files = {}

    def write_file(self, path, content):
        self.files[str(path)] = content

def test_add_node_creates_files():
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier
    )

    result = use_case.execute(title="Chapter One")

    assert len(fs.files) == 2  # draft + notes
    assert "draft" in list(fs.files.keys())[0]
    assert "notes" in list(fs.files.keys())[1]
```

2. **Run test** (FAIL)
3. **Implement** `src/linemark/use_cases/add_node.py`
4. **Run test** (PASS)

Repeat for:
- MoveNode
- DeleteNode
- RenameNode
- ListOutline
- CompactOutline
- ValidateOutline (doctor)
- ManageTypes

**Success Criteria**: All use cases tested with fake adapters, 100% coverage

---

### Phase 5: CLI Layer (Thin Click Wrapper)

**Test File**: `tests/integration/test_cli.py`

**TDD Steps**:

1. **Write CLI integration test**:
```python
from click.testing import CliRunner
from linemark.cli.main import lmk

def test_add_command_integration(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(lmk, ['add', 'Chapter One'])

        assert result.exit_code == 0
        assert "001_" in result.output
```

2. **Run test** (FAIL)
3. **Implement** `src/linemark/cli/main.py` with Click decorators
4. **Wire up** use cases with real adapters
5. **Run test** (PASS)

Repeat for all commands.

**Success Criteria**: All CLI commands work end-to-end

---

### Phase 6: Integration Tests (Complete Workflows)

**Test Files**: `tests/integration/test_*_workflow.py`

**TDD Steps**:

1. **Test complete add → list workflow**:
```python
def test_add_then_list_workflow(tmp_path):
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Add nodes
        runner.invoke(lmk, ['add', 'Chapter One'])
        runner.invoke(lmk, ['add', 'Chapter Two'])

        # List
        result = runner.invoke(lmk, ['list'])

        assert "Chapter One" in result.output
        assert "Chapter Two" in result.output
```

2. **Test move workflow** (add → move → verify)
3. **Test delete workflows** (recursive, promote)
4. **Test doctor workflow** (corrupt → repair)

**Success Criteria**: All user stories from spec.md verified end-to-end

---

## Quality Gates (Pre-Commit)

### Run All Tests

```bash
pytest --cov=src/linemark --cov-report=term-missing
```

**Required**: 100% coverage (constitution § III)

### Type Check

```bash
mypy src/ --strict
```

**Required**: Zero mypy errors (constitution § III)

### Lint

```bash
ruff check src/ tests/
```

**Required**: Zero ruff violations (constitution § III)

---

## Implementation Tips

### 1. Start Small

Build one vertical slice at a time:
- MaterializedPath value object
- FileSystemAdapter
- AddNode use case
- `lmk add` command

Don't try to build everything at once.

### 2. Use Fakes in Unit Tests

Create simple fake adapters for testing:

```python
class FakeSQIDGenerator:
    def __init__(self):
        self.counter = 0

    def encode(self, n):
        return f"SQID{n}"
```

### 3. Leverage tmp_path Fixture

Use pytest's `tmp_path` for filesystem tests:

```python
def test_filesystem_adapter(tmp_path):
    adapter = FileSystemAdapter()
    file = tmp_path / "test.md"
    # Test with real filesystem in isolated temp directory
```

### 4. Test Error Cases

Don't just test happy paths:

```python
def test_add_node_at_999_limit_fails():
    # Create outline with 999 siblings
    # Attempt to add another
    # Assert raises MaterializedPathExhaustedError
```

### 5. Refactor Fearlessly

With 100% test coverage, refactoring is safe:
- Extract helper methods
- Rename for clarity
- Simplify complex logic

Tests will catch any regressions.

---

## Checkpoint Milestones

| Milestone | Definition of Done |
|-----------|-------------------|
| **M1: Domain Complete** | All value objects, entities, outline tested at 100% |
| **M2: Ports & Adapters** | All ports defined, adapters implemented, contract tests pass |
| **M3: Use Cases** | All 8 use cases implemented with fake adapter tests |
| **M4: CLI Working** | All commands wired up, integration tests pass |
| **M5: Quality Gates** | 100% coverage, mypy strict, ruff clean |
| **M6: MVP Complete** | All user stories verified, documentation complete |

---

## Next Steps

After completing this quickstart:

1. **Generate tasks**: Run `/speckit.tasks` to create detailed task breakdown
2. **Begin implementation**: Follow TDD discipline strictly
3. **Iterate**: Red → Green → Refactor for each component
4. **Verify**: Run quality gates after each milestone

**Remember**: Tests before implementation, always. No exceptions.
