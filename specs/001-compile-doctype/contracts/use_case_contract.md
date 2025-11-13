# Use Case Contract: CompileDoctypeUseCase

**Feature**: `001-compile-doctype`
**Component**: `linemark.use_cases.compile_doctype.CompileDoctypeUseCase`
**Date**: 2025-11-13

## Purpose

Orchestrates the compilation of all doctype files from a forest or subtree, producing a single concatenated output with configurable separators.

## Interface Specification

### Constructor

```python
class CompileDoctypeUseCase:
    def __init__(self, filesystem: FileSystem) -> None:
        """Initialize use case with filesystem port.

        Args:
            filesystem: Port for file system operations
        """
```

**Contract**:
- MUST accept FileSystem port via dependency injection
- MUST NOT perform I/O in constructor
- MUST NOT raise exceptions in constructor

### Primary Method: execute

```python
def execute(
    self,
    doctype: str,
    directory: Path,
    sqid: str | None = None,
    separator: str = '\n\n---\n\n',
) -> str:
    """Compile all doctype files into single output.

    Args:
        doctype: Name of doctype to compile (e.g., 'draft', 'notes')
        directory: Working directory containing the forest
        sqid: Optional SQID to limit to subtree (None = entire forest)
        separator: Separator between documents (escape sequences interpreted)

    Returns:
        Compiled content as string (empty string if no content found)

    Raises:
        DoctypeNotFoundError: If doctype doesn't exist in compilation scope
        NodeNotFoundError: If sqid provided but node doesn't exist
        FileSystemError: If file system operations fail
        InvalidPathError: If directory path is invalid
    """
```

**Behavioral Contract**:

1. **Input Validation**:
   - MUST validate `doctype` is non-empty string
   - MUST validate `directory` is valid Path
   - MUST validate `sqid` format if provided (alphanumeric)
   - MUST interpret escape sequences in `separator` (`\n` → newline, etc.)

2. **Node Collection**:
   - MUST retrieve all nodes from `directory` via `filesystem.list_outline()`
   - IF `sqid` provided, MUST filter to subtree (specified node + descendants)
   - MUST maintain lexicographical ordering (provided by list_outline)

3. **Doctype Validation**:
   - MUST scan collected nodes for doctype file existence
   - MUST raise `DoctypeNotFoundError` if NO nodes have the doctype file
   - This validation MUST happen before reading any file content

4. **Content Collection**:
   - FOR EACH node in order:
     - Check if `{node.directory}/{doctype}.md` exists
     - IF exists AND non-empty (not whitespace-only):
       - Read file content
       - Append to output collection
   - MUST skip nodes without doctype file (silently)
   - MUST skip empty/whitespace-only files (silently)

5. **Output Generation**:
   - IF no content collected, MUST return empty string ""
   - IF content collected, MUST join with processed separator
   - MUST NOT add separator before first item or after last item
   - Separator MUST appear BETWEEN items only

6. **Error Handling**:
   - MUST propagate file system errors as `FileSystemError`
   - MUST provide context in error messages (which file, operation)
   - MUST handle UTF-8 decode errors gracefully (log warning, skip file)

## Preconditions

- `filesystem` port MUST be provided and functional
- `directory` MUST exist and be readable
- IF `sqid` provided, corresponding node MUST exist in outline

## Postconditions

- No files are modified (read-only operation)
- Result is deterministic (same inputs → same output)
- If successful, result contains compiled content or empty string
- If error, appropriate exception is raised with context

## Example Scenarios

### Scenario 1: Compile Entire Forest

**Given**:
```
Forest structure:
001/draft.md: "Chapter 1"
001-001/draft.md: "Section 1.1"
002/draft.md: "Chapter 2"

Input:
- doctype="draft"
- directory=Path("/forest")
- sqid=None
- separator="\n---\n"
```

**Then**:
```
Output: "Chapter 1\n---\nSection 1.1\n---\nChapter 2"
```

### Scenario 2: Compile Subtree

**Given**:
```
Forest structure:
001/@Gxn7qZp/draft.md: "Chapter 1"
001-001/@abc123/draft.md: "Section 1.1"
002/@def456/draft.md: "Chapter 2"

Input:
- doctype="draft"
- directory=Path("/forest")
- sqid="Gxn7qZp"
- separator="\n---\n"
```

**Then**:
```
Output: "Chapter 1\n---\nSection 1.1"
(Only node Gxn7qZp and its descendants)
```

### Scenario 3: Empty Files Skipped

**Given**:
```
Forest structure:
001/draft.md: "Chapter 1"
002/draft.md: "   \n  \n"  (whitespace only)
003/draft.md: "Chapter 3"

Input:
- doctype="draft"
- separator="\n---\n"
```

**Then**:
```
Output: "Chapter 1\n---\nChapter 3"
(Node 002 skipped - empty content)
```

### Scenario 4: Doctype Not Found

**Given**:
```
Forest structure:
001/draft.md: "Content"
002/draft.md: "Content"
(No "notes.md" files exist)

Input:
- doctype="notes"
```

**Then**:
```
Raises: DoctypeNotFoundError("Doctype 'notes' not found in forest...")
```

### Scenario 5: No Content (All Empty)

**Given**:
```
Forest structure:
001/draft.md: ""
002/draft.md: "  "

Input:
- doctype="draft"
```

**Then**:
```
Output: ""
(Empty string - all files were empty/whitespace)
```

## Performance Expectations

- **Small forests** (< 100 nodes): < 100ms
- **Medium forests** (100-1000 nodes): < 1 second
- **Large forests** (1000-10000 nodes): < 10 seconds
- Memory usage: O(n) where n = total size of compiled content
- No caching or indexing required initially

## Thread Safety

- NOT thread-safe (single-threaded CLI use case)
- If concurrent access needed in future, use case instances should not be shared

## Testability Requirements

- MUST be testable with fake FileSystem adapter
- MUST NOT depend on real file system in unit tests
- Integration tests MAY use real file system
- All edge cases MUST be covered by unit tests:
  - Empty forest
  - Missing doctype
  - Empty files
  - Subtree filtering
  - Escape sequence handling
  - Various separator values
