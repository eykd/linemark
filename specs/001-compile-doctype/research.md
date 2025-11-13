# Research: Compile Doctype Command

**Feature**: `001-compile-doctype`
**Date**: 2025-11-13
**Phase**: 0 - Outline & Research

## Research Questions & Findings

### Q1: How to efficiently traverse and collect doctype files from the forest?

**Decision**: Use existing FileSystem port methods with lexicographical ordering

**Rationale**:
- The existing `FileSystemAdapter.list_outline()` method already returns nodes sorted by materialized path
- MaterializedPath's lexicographical ordering (001-002-003) naturally provides depth-first traversal
- No need for complex tree traversal algorithms - simple iteration over sorted list works
- Memory efficient for typical forests (< 10,000 nodes)

**Alternatives considered**:
- Custom tree traversal: Rejected - unnecessary complexity when sorted list provides same ordering
- Database/index: Rejected - violates plain text storage principle and adds infrastructure complexity
- Streaming directory scan: Rejected - less reliable ordering, more complex error handling

### Q2: How should escape sequences be interpreted in custom separators?

**Decision**: Use Python's built-in `codecs.decode()` with 'unicode_escape' codec

**Rationale**:
- Standard library solution - no external dependencies
- Handles common escape sequences: `\n` (newline), `\t` (tab), `\\` (backslash), etc.
- Consistent with Unix tool behavior (echo -e, printf)
- Well-documented and tested approach

**Alternatives considered**:
- Manual string replacement: Rejected - error-prone, incomplete coverage of edge cases
- Template strings: Rejected - overpowered for simple escape sequence needs
- No interpretation (literal): Rejected - less flexible, doesn't match user expectations from clarifications

**Implementation note**:
```python
separator = separator.encode().decode('unicode_escape')
```

### Q3: How to efficiently skip empty/whitespace-only files without loading large files into memory?

**Decision**: Use file size check + peek first bytes strategy

**Rationale**:
- Zero-byte files: Skip immediately via `Path.stat().st_size == 0`
- Non-zero files: Read first 1KB, check if all whitespace - if yes, likely empty throughout
- For files with content in first 1KB: Read full file (they're not empty)
- Balances performance with correctness for typical use cases

**Alternatives considered**:
- Always read full file: Rejected - wasteful for large empty files (could be 10MB of whitespace)
- Only check file size: Rejected - doesn't catch whitespace-only files
- Stream and check while reading: Rejected - more complex, minimal benefit for typical file sizes

**Implementation note**:
```python
def is_empty_content(file_path: Path) -> bool:
    if file_path.stat().st_size == 0:
        return True
    # Peek first 1KB
    with file_path.open('r', encoding='utf-8') as f:
        sample = f.read(1024)
        if sample.isspace() or not sample:
            return True
    return False
```

### Q4: How to validate doctype exists before attempting compilation?

**Decision**: Pre-scan forest to collect available doctypes, validate before compilation

**Rationale**:
- Fast fail principle - validate early, provide clear error messages
- Prevents wasted work traversing entire forest only to produce nothing
- Enables informative error: "Doctype 'draf' not found. Did you mean 'draft'?" (future enhancement)
- Minimal performance cost for typical forests

**Alternatives considered**:
- Compile and check if empty: Rejected - can't distinguish "no content" from "typo in doctype name"
- No validation: Rejected - violates FR-011, poor user experience
- Database/index of doctypes: Rejected - adds complexity, violates plain text principle

**Implementation approach**:
1. Iterate through relevant nodes (forest or subtree)
2. Check each node directory for files matching `<doctype>.md`
3. If at least one found, doctype exists - proceed
4. If none found, raise DoctypeNotFoundError with helpful message

### Q5: What's the best pattern for implementing the use case given existing codebase patterns?

**Decision**: Follow existing `ListOutlineUseCase` pattern with minor adaptations

**Rationale**:
- Consistency with codebase conventions
- Proven pattern already tested and working
- Constructor injection of FileSystem port
- Public `execute()` method returns result
- Validation in use case, I/O in adapter

**Reference pattern** (from existing codebase):
```python
class CompileDoctypeUseCase:
    def __init__(self, filesystem: FileSystem) -> None:
        self.filesystem = filesystem

    def execute(
        self,
        doctype: str,
        sqid: str | None,
        separator: str,
        directory: Path
    ) -> str:
        # 1. Validate inputs
        # 2. Get nodes (forest or subtree)
        # 3. Validate doctype exists
        # 4. Collect & concatenate content
        # 5. Return result
```

### Q6: How to handle potential Unicode encoding issues in doctype files?

**Decision**: UTF-8 by default with fallback error handling

**Rationale**:
- UTF-8 is standard for modern markdown files
- Python's default encoding on modern systems
- Edge case: If decode fails, skip file with warning to stderr (graceful degradation)
- Matches existing FileSystem adapter patterns

**Alternatives considered**:
- Strict UTF-8 only: Rejected - too brittle, one bad file breaks entire compilation
- Auto-detect encoding: Rejected - adds complexity and dependencies (chardet), overkill for typical use
- Binary mode: Rejected - loses ability to validate whitespace-only files

## Technology Decisions Summary

| Decision Area | Choice | Justification |
|---------------|--------|---------------|
| Traversal Strategy | Lexicographical sorting | Leverages existing MaterializedPath ordering |
| Escape Sequences | `codecs.decode('unicode_escape')` | Standard library, well-tested |
| Empty File Detection | Size check + 1KB peek | Balances performance and correctness |
| Doctype Validation | Pre-scan before compilation | Fast fail, better UX |
| Use Case Pattern | Match existing patterns | Consistency, proven approach |
| Encoding Handling | UTF-8 with graceful fallback | Standard, practical error handling |

## Dependencies

**No new dependencies required** - feature uses only existing dependencies:
- Click: CLI framework (already in use)
- Pydantic: Validation (already in use)
- pathlib: File operations (standard library)
- codecs: Escape sequence handling (standard library)

## Performance Considerations

**Expected Performance**:
- 1,000 nodes with 50% having doctype: ~0.5-1 second
- 10,000 nodes with 50% having doctype: ~5-10 seconds
- Bottleneck: File I/O (reading doctype files)
- Acceptable for CLI tool targeting human-scale workflows

**Optimization Opportunities** (if needed in future):
- Parallel file reading (concurrent.futures)
- Memory-mapped files for very large documents
- Caching of file metadata

## Integration Points

1. **FileSystem Port**: Use existing `list_outline()`, file reading methods
2. **CLI Main**: Add new `@lmk.command()` following existing patterns
3. **Domain Entities**: Use existing `MaterializedPath`, `Node` entities
4. **Error Handling**: Use existing `DomainException` subclasses, add new `DoctypeNotFoundError`

## Open Questions / Future Enhancements

1. **Corrupted outline handling**: Defer to existing `validate_outline` command
2. **Non-UTF-8 encodings**: Handle gracefully with warnings (edge case)
3. **Progress reporting**: Could add `--verbose` flag for large compilations (future)
4. **Output to file**: Currently stdout only, could add `--output` flag (future)
5. **Doctype suggestion on typo**: "Did you mean 'draft'?" (future enhancement)
