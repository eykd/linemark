# Research: Node and Document Type Operations

**Feature**: 001-node-doctype-commands
**Date**: 2025-11-15

## Overview

This document captures technical research and decisions for implementing three new CLI commands: `lmk types read`, `lmk types write`, and `lmk search`.

## Research Areas

### 1. Atomic File Writes in Python

**Decision**: Use `tempfile.NamedTemporaryFile` + `os.replace()` pattern

**Rationale**:
- `os.replace()` is atomic on POSIX and Windows (Python 3.3+)
- `tempfile.NamedTemporaryFile` handles temp file creation/cleanup
- Prevents partial writes from corrupting existing files
- Standard pattern used across Python ecosystem

**Implementation Pattern**:
```python
import tempfile
import os
from pathlib import Path

def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically."""
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=path.parent,
        delete=False,
        encoding='utf-8'
    ) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    os.replace(tmp_path, path)
```

**Alternatives Considered**:
- Direct file.write() - rejected: not atomic, risky
- Write-then-rename manually - rejected: tempfile handles cleanup better
- File locking - rejected: unnecessary complexity for single-writer scenario

### 2. YAML Frontmatter Preservation

**Decision**: Use PyYAML with custom loader/dumper to preserve formatting

**Rationale**:
- PyYAML already in dependencies (6.0.2+)
- Can separate frontmatter from body using `---` delimiters
- Preserve original YAML formatting when updating body only

**Implementation Pattern**:
```python
import yaml

def read_with_frontmatter(content: str) -> tuple[dict, str]:
    """Split content into frontmatter and body."""
    if not content.startswith('---\n'):
        return {}, content

    parts = content.split('---\n', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter = yaml.safe_load(parts[1])
    body = parts[2]
    return frontmatter, body

def write_with_frontmatter(frontmatter: dict, body: str) -> str:
    """Combine frontmatter and body."""
    yaml_str = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
    return f"---\n{yaml_str}---\n{body}"
```

**Alternatives Considered**:
- python-frontmatter library - rejected: adds dependency for simple task
- Regex parsing - rejected: fragile, doesn't preserve YAML structure
- Manual string splitting only - chosen: simple, reliable, uses existing PyYAML

### 3. Regex Search with Python `re` Module

**Decision**: Use `re.compile()` with flags, search line-by-line by default

**Rationale**:
- Python's `re` module is stdlib, performant, well-documented
- Compile regex once, reuse across files (performance)
- Case-insensitive: `re.IGNORECASE` flag
- Multiline: `re.DOTALL` flag (opt-in via `--multiline`)
- Literal matching: `re.escape()` for `--literal` flag

**Implementation Pattern**:
```python
import re

def create_search_pattern(
    pattern: str,
    case_sensitive: bool = False,
    multiline: bool = False,
    literal: bool = False
) -> re.Pattern:
    """Create compiled regex pattern with appropriate flags."""
    if literal:
        pattern = re.escape(pattern)

    flags = 0
    if not case_sensitive:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.DOTALL

    return re.compile(pattern, flags)
```

**Alternatives Considered**:
- ripgrep via subprocess - rejected: external dependency, overkill for Python tool
- fnmatch module - rejected: limited to glob patterns, not regex
- Custom regex engine - rejected: reinventing stdlib, unnecessary

### 4. Outline Position Ordering

**Decision**: Use existing filename-based hierarchical ordering (depth-first traversal)

**Rationale**:
- Linemark already uses filename-based ordering (NNN-NNN-NNN_SQID_doctype_slug.md pattern)
- Files naturally sort in hierarchical order when listing directory
- Existing `list_outline.py` use case provides this ordering logic
- Depth-first traversal matches user mental model of outline

**Implementation Pattern**:
```python
from pathlib import Path

def get_files_in_outline_order(directory: Path) -> list[Path]:
    """Get all markdown files sorted by outline position."""
    files = sorted(directory.glob('*.md'))
    # Files already in correct order due to NNN-NNN-NNN prefix
    return files
```

**Alternatives Considered**:
- Alphabetical by SQID - rejected: loses hierarchical context
- Most recently modified - rejected: loses outline structure
- Custom ordering metadata - rejected: filename encoding is sufficient

### 5. Search Result Format

**Decision**: Plaintext by default, JSON optional

**Plaintext Format**:
```
@SQID: filename.md
LINE_NUM: matching line content
```

**JSON Format**:
```json
[
  {
    "sqid": "ABC123",
    "filename": "100-200-300_ABC123_notes_chapter-1.md",
    "line_number": 42,
    "content": "matching line content"
  }
]
```

**Rationale**:
- Plaintext is grep-like, familiar to CLI users
- JSON enables programmatic consumption
- Both formats easy to parse
- Follows CLI-first principle (text in, text out)

**Alternatives Considered**:
- Only JSON - rejected: less human-friendly for direct CLI use
- XML - rejected: overly verbose for simple data
- Custom DSL - rejected: JSON is standard, widely supported

### 6. Error Handling Strategy

**Decision**: Raise domain-specific exceptions, handle at CLI boundary

**Exception Types**:
- `NodeNotFoundError` (existing) - SQID doesn't exist
- `DoctypeNotFoundError` (existing) - doctype file doesn't exist
- `InvalidRegexError` (new) - regex pattern is invalid
- `SearchError` (new) - generic search failures

**Rationale**:
- Domain exceptions express business rules
- CLI layer catches and converts to user-friendly messages + exit codes
- Follows existing linemark error handling pattern
- Maintains hexagonal architecture (domain doesn't know about CLI)

**Implementation Pattern**:
```python
# domain/exceptions.py
class InvalidRegexError(Exception):
    """Raised when regex pattern is invalid."""

# cli/main.py
try:
    result = use_case.execute(...)
except InvalidRegexError as e:
    click.echo(f"Error: Invalid regex pattern: {e}", err=True)
    sys.exit(1)
```

**Alternatives Considered**:
- Return Result[T, E] type - rejected: not idiomatic Python
- Raise generic exceptions - rejected: loses semantic meaning
- Silent failures - rejected: violates fail-fast principle

### 7. Performance Considerations

**Decision**: Stream processing for large files, lazy evaluation where possible

**Strategies**:
- Read files line-by-line for search (don't load entire file to memory)
- Use generators for file iteration
- Compile regex once, reuse across files
- Only load full content when necessary (e.g., write operations)

**Implementation Pattern**:
```python
def search_file(path: Path, pattern: re.Pattern) -> Iterator[tuple[int, str]]:
    """Search file line-by-line, yield matches."""
    with path.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            if pattern.search(line):
                yield (line_num, line.rstrip('\n'))
```

**Rationale**:
- Supports MB+ files without memory issues
- Meets performance goals (1000+ nodes in <5s)
- Lazy evaluation reduces unnecessary work

**Alternatives Considered**:
- Load all files to memory - rejected: doesn't scale to large outlines
- Database indexing - rejected: violates plain text storage principle
- Parallel processing - deferred: optimize if needed, keep simple first

## Technology Decisions Summary

| Area | Technology | Version | Rationale |
|------|------------|---------|-----------|
| Atomic Writes | `tempfile` + `os.replace()` | stdlib | POSIX/Windows atomic, reliable |
| YAML Parsing | PyYAML | 6.0.2+ | Already in deps, standards-compliant |
| Regex Engine | Python `re` module | stdlib | Performant, well-documented |
| CLI Framework | Click | 8.1.8+ | Already in use, consistent with codebase |
| File Iteration | Pathlib + generators | stdlib | Memory efficient, pythonic |

## Best Practices Applied

### Hexagonal Architecture
- Domain logic (search matching, path resolution) independent of I/O
- Ports define contracts (ReadTypePort, WriteTypePort, SearchPort)
- Adapters implement concrete I/O (filesystem, regex)
- Use cases orchestrate domain + ports

### Test-First Development
- Contract tests verify port protocols
- Unit tests verify use case logic in isolation
- Integration tests verify end-to-end CLI workflows
- All tests written before implementation

### Code Quality
- 100% test coverage required
- 100% mypy strict mode (full type annotations)
- 100% ruff linting (comprehensive ruleset)
- Docstrings for all public APIs (Google style)

### CLI Design
- stdin/stdout for data flow
- stderr for errors
- Exit codes: 0 success, 1 error
- Support both human-readable and machine-parsable formats
- Composable with Unix tools (pipes, redirection)

## Open Questions

*None - all technical unknowns resolved*

## References

- Python `re` module: https://docs.python.org/3/library/re.html
- Python `tempfile` module: https://docs.python.org/3/library/tempfile.html
- PyYAML documentation: https://pyyaml.org/wiki/PyYAMLDocumentation
- Atomic file operations: https://www.notthewizard.com/2014/06/17/are-files-appends-really-atomic/
- Click documentation: https://click.palletsprojects.com/
