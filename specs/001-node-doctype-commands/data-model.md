# Data Model: Node and Document Type Operations

**Feature**: 001-node-doctype-commands
**Date**: 2025-11-15

## Overview

This document defines the data structures, entities, and file formats for the node and document type operations feature.

## Entities

### SearchResult

Represents a single search match found in the outline.

**Attributes**:
- `sqid`: str - The SQID of the node containing the match
- `filename`: str - Full filename of the document type file
- `line_number`: int - Line number where match was found (1-indexed)
- `content`: str - The matching line content (without newline)
- `path`: Path - Full path to the file (for internal use)

**Validation Rules**:
- `sqid` must be non-empty string
- `filename` must be valid markdown filename
- `line_number` must be positive integer >= 1
- `content` must be non-empty string (matched lines can't be blank)
- `path` must be absolute Path object

**State Transitions**: None (immutable value object)

**Example**:
```python
SearchResult(
    sqid="ABC123",
    filename="100-200-300_ABC123_notes_chapter-1.md",
    line_number=42,
    content="The quick brown fox jumps over the lazy dog",
    path=Path("/workspace/100-200-300_ABC123_notes_chapter-1.md")
)
```

### DocumentTypeContent

Represents the content of a document type file split into frontmatter and body.

**Attributes**:
- `frontmatter`: dict[str, Any] - YAML frontmatter as dictionary
- `body`: str - Document body content (everything after second `---`)

**Validation Rules**:
- `frontmatter` must be valid YAML dict (can be empty {})
- `body` must be string (can be empty "")

**State Transitions**: None (immutable value object)

**Example**:
```python
DocumentTypeContent(
    frontmatter={
        "sqid": "ABC123",
        "doctype": "notes",
        "title": "Chapter 1: Introduction"
    },
    body="This is the chapter content.\n\nIt has multiple paragraphs."
)
```

### SearchPattern

Encapsulates compiled regex pattern with search options.

**Attributes**:
- `pattern`: re.Pattern - Compiled regex pattern
- `case_sensitive`: bool - Whether search is case-sensitive
- `multiline`: bool - Whether search spans multiple lines
- `literal`: bool - Whether pattern is literal (non-regex)
- `original_pattern`: str - Original pattern string (for error messages)

**Validation Rules**:
- `pattern` must be valid compiled regex (raises InvalidRegexError if compilation fails)
- `case_sensitive`, `multiline`, `literal` must be bool
- `original_pattern` must match the input pattern string

**State Transitions**: None (immutable value object created from string pattern)

**Example**:
```python
SearchPattern(
    pattern=re.compile(r'foo.*bar', re.IGNORECASE),
    case_sensitive=False,
    multiline=False,
    literal=False,
    original_pattern="foo.*bar"
)
```

## File Format

### Document Type File Structure

All document type files follow this structure:

```markdown
---
sqid: ABC123
doctype: notes
title: Example Title
slug: example-title
position: 100-200-300
created: 2025-11-15T10:00:00Z
modified: 2025-11-15T10:00:00Z
---
Body content starts here.

This is the actual document content that users edit.

Multiple paragraphs and formatting are preserved.
```

**Format Rules**:
- YAML frontmatter enclosed in `---` delimiters
- Frontmatter contains metadata (sqid, doctype, title, etc.)
- Body is everything after the second `---` delimiter
- Encoding: UTF-8
- Line endings: normalized to `\n` (Unix-style)

### Filename Convention

Existing linemark convention:

```
NNN-NNN-NNN_SQID_DOCTYPE_SLUG.md
```

**Components**:
- `NNN-NNN-NNN`: Position path (hierarchical sorting)
- `SQID`: Unique identifier (from sqids library)
- `DOCTYPE`: Document type (e.g., notes, characters, scenes)
- `SLUG`: URL-friendly title slug
- `.md`: Markdown extension

**Example**:
```
100-200-300_ABC123_notes_chapter-1-introduction.md
```

## Data Relationships

### Node → Document Type (1:N)

```
Node (identified by SQID)
  ├── notes file (optional)
  ├── characters file (optional)
  ├── scenes file (optional)
  └── [custom doctype] file (optional)
```

- One node (SQID) can have multiple document type files
- Each doctype for a node has exactly one file
- Files share the same position prefix and SQID
- Files differ only in DOCTYPE and SLUG components

**Example**:
```
100-200-300_ABC123_notes_chapter-1.md
100-200-300_ABC123_characters_protagonist.md
100-200-300_ABC123_scenes_opening.md
```

### Outline Hierarchy

```
Outline (directory)
  ├── 100_SQID1_notes_root.md
  ├── 100-100_SQID2_notes_child1.md
  ├── 100-200_SQID3_notes_child2.md
  │   ├── 100-200-100_SQID4_notes_grandchild1.md
  │   └── 100-200-200_SQID5_notes_grandchild2.md
  └── 200_SQID6_notes_root2.md
```

**Ordering**:
- Lexicographic sort by filename
- Position prefix ensures hierarchical ordering
- Depth-first traversal when iterating

## Search Data Flow

### Input → Processing → Output

```
User Input
  ↓
Pattern String + Flags (--case-sensitive, --multiline, --literal)
  ↓
SearchPattern (compiled regex)
  ↓
SearchUseCase
  ↓
For each file in outline order:
  ↓
  SearchPort.search_file(path, pattern)
    ↓
    For each line:
      ↓
      Match? → Create SearchResult
  ↓
Collect all SearchResult objects
  ↓
Format as plaintext or JSON
  ↓
Output to stdout
```

## Read/Write Data Flow

### Read Flow

```
User: lmk types read DOCTYPE @SQID
  ↓
ReadTypeUseCase
  ↓
ReadTypePort.resolve_file_path(sqid, doctype, directory)
  ↓
FileSystemPort.read_file(path)
  ↓
Parse YAML frontmatter and body
  ↓
Return body only
  ↓
Output to stdout
```

### Write Flow

```
User: echo "content" | lmk types write DOCTYPE @SQID
  ↓
Read stdin → content string
  ↓
WriteTypeUseCase
  ↓
WriteTypePort.resolve_file_path(sqid, doctype, directory)
  ↓
If file exists:
  ↓
  Read existing file → extract frontmatter
  ↓
  Combine frontmatter + new body
Else:
  ↓
  Create minimal frontmatter (sqid, doctype)
  ↓
  Combine frontmatter + new body
  ↓
WriteTypePort.write_file_atomic(path, content)
  ↓
Atomic write (tempfile → rename)
  ↓
Success (no output, exit 0)
```

## Error States

### Search Errors

| Error Type | Condition | User Message |
|------------|-----------|--------------|
| InvalidRegexError | Regex pattern doesn't compile | "Invalid regex pattern: [error details]" |
| NodeNotFoundError | SQID doesn't exist in outline | "Node @SQID not found in outline" |
| DoctypeNotFoundError | No files match doctype filter | "No files found for doctype: [doctype]" |

### Read Errors

| Error Type | Condition | User Message |
|------------|-----------|--------------|
| NodeNotFoundError | SQID doesn't exist | "Node @SQID not found" |
| DoctypeNotFoundError | Doctype file doesn't exist for node | "Document type '[doctype]' not found for node @SQID" |
| PermissionError | File not readable | "Permission denied reading file: [path]" |
| UnicodeDecodeError | File not valid UTF-8 | "Invalid UTF-8 encoding in file: [path]" |

### Write Errors

| Error Type | Condition | User Message |
|------------|-----------|--------------|
| NodeNotFoundError | SQID doesn't exist | "Node @SQID not found" |
| PermissionError | File/directory not writable | "Permission denied writing file: [path]" |
| OSError (disk full) | No space left on device | "Disk full, cannot write file: [path]" |
| FileNotFoundError | Directory doesn't exist | "Directory not found: [path]" |

## JSON Output Schema

### Search Results JSON

```json
[
  {
    "sqid": "ABC123",
    "filename": "100-200-300_ABC123_notes_chapter-1.md",
    "line_number": 42,
    "content": "matching line content"
  },
  {
    "sqid": "DEF456",
    "filename": "100-200-400_DEF456_characters_protagonist.md",
    "line_number": 7,
    "content": "another matching line"
  }
]
```

**Schema Definition**:
```python
from typing import TypedDict

class SearchResultJSON(TypedDict):
    sqid: str
    filename: str
    line_number: int
    content: str
```

## Volume and Scale

### Expected Data Characteristics

- **Number of nodes**: 10 to 10,000+
- **File size**: 1 KB to 10 MB per document type file
- **Doctypes per node**: 1 to 10 (typically 1-3)
- **Total files**: 10 to 50,000+
- **Outline depth**: 1 to 10 levels (typically 3-5)

### Performance Targets

- **Read operation**: < 2 seconds for any file size
- **Write operation**: < 3 seconds for any file size (including atomic write)
- **Search operation**: < 5 seconds for 1000+ nodes
- **Memory usage**: < 100 MB for search across 1000 nodes

### Scalability Considerations

- Stream processing (line-by-line) for search prevents memory issues
- Atomic writes use same-filesystem temp files (fast rename)
- File iteration uses generators (lazy evaluation)
- Regex compiled once, reused across all files
