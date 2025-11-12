# Linemark Port Contracts

This directory contains the port interfaces (contracts) that define the boundaries between Linemark's domain logic and external dependencies.

## Purpose

Following hexagonal architecture (Constitution § I), ports are **protocol definitions** that:
- Define what capabilities the domain logic requires from infrastructure
- Enable testing domain logic without real filesystem, SQID library, etc.
- Allow swapping implementations (e.g., in-memory filesystem for tests)
- Make dependencies explicit and testable

## Contracts

### `filesystem_port.py`
Defines operations for reading, writing, deleting, and listing markdown files. Isolates domain from pathlib/OS specifics.

**Key Operations**:
- `read_file()`, `write_file()`, `delete_file()` - Basic file operations
- `rename_file()` - Atomic rename for move operations
- `list_markdown_files()` - Scan directory for .md files
- `file_exists()`, `create_directory()` - Utilities

**Error Handling**: All methods raise descriptive exceptions on failure (fail-fast per FR-042).

### `sqid_generator_port.py`
Defines interface for encoding integers to short identifiers (SQIDs). Isolates domain from sqids library.

**Key Operations**:
- `encode(counter)` - Convert integer to SQID string
- `decode(sqid)` - Convert SQID back to integer (for counter derivation)

**Determinism**: Same input always produces same output (critical for testing).

### `slugifier_port.py`
Defines interface for converting titles to URL-safe slugs. Isolates domain from python-slugify library.

**Key Operations**:
- `slugify(text)` - Convert arbitrary text to kebab-case slug

**Determinism**: Same input always produces same output (critical for testing).

## Usage in Tests

### Contract Tests (`tests/contract/`)
Verify that concrete adapters correctly implement port protocols:

```python
def test_filesystem_adapter_implements_port():
    adapter = FileSystemAdapter()
    assert isinstance(adapter, FileSystemPort)
    # Test each method signature...
```

### Unit Tests with Fakes (`tests/unit/`)
Test domain logic using fake adapters:

```python
class FakeFileSystem:
    def __init__(self):
        self.files = {}

    def read_file(self, path):
        return self.files.get(path, "")

    def write_file(self, path, content):
        self.files[path] = content

def test_add_node_use_case():
    fs = FakeFileSystem()
    use_case = AddNodeUseCase(filesystem=fs, ...)
    use_case.execute(title="Chapter One")
    assert "001_" in fs.files  # Verify file created
```

## Implementation Adapters

Concrete implementations live in `src/linemark/adapters/`:
- `adapters/filesystem.py` - PathLib-based implementation
- `adapters/sqid_generator.py` - sqids library wrapper
- `adapters/slugifier.py` - python-slugify wrapper

Each adapter must satisfy its corresponding port contract and pass contract tests.
