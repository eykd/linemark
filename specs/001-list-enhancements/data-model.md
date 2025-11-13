# Data Model: Enhanced List Command

**Feature**: 001-list-enhancements
**Date**: 2025-11-13
**Status**: Complete

## Overview

This feature extends the existing `lmk list` command without modifying the core data model. All necessary data already exists in the `Node` entity. This document describes how existing data is used and what computed values are derived for display purposes.

---

## Existing Domain Entities (No Changes)

### Node

**Purpose**: Represents a logical entry in the outline hierarchy, aggregating all document files for a position.

**Source**: `src/linemark/domain/entities.py`

**Attributes** (existing):
```python
class Node(BaseModel):
    sqid: SQID                      # Stable unique identifier
    mp: MaterializedPath            # Hierarchical position (e.g., "001-100-050")
    title: str                      # Canonical title from draft frontmatter
    slug: str                       # URL-friendly slug from title
    document_types: set[str]        # Document types present (e.g., {"draft", "notes"})
```

**Relevant Methods** (existing):
- `filename(doc_type: str) -> str`: Generates filename for a given document type
  - Format: `<mp>_<sqid>_<type>_<slug>.md`
  - Example: `001-100_A3F7c_draft_my-chapter.md`

- `filenames() -> list[str]`: Returns all filenames for this node (sorted by doctype)

**Usage for This Feature**:
- `document_types`: Used directly for `--show-doctypes` display
- `filenames()`: Used to compute relative paths for `--show-files` display
- `sqid`: Used for subtree filtering argument
- `mp`: Used to filter descendants when displaying subtree

---

## Computed Display Values (Not Stored)

These values are computed at display time in the presentation layer (formatters).

### Doctype Display String

**Computation**:
```python
doctype_str = ", ".join(sorted(node.document_types))
```

**Example**: `"draft, notes"` or `"draft, notes, outline, research"`

**Display Context**:
- Tree text output: `├─ doctypes: draft, notes`
- JSON output: `"doctypes": ["draft", "notes"]` (as array)

**Edge Cases**:
- Empty set → omit metadata line entirely (per clarifications)
- Single doctype → display as-is (e.g., `"draft"`)

---

### File Path List

**Computation**:
```python
file_paths = [
    Path(directory) / node.filename(dt)
    for dt in sorted(node.document_types)
]
relative_paths = [p.relative_to(directory) for p in file_paths]
```

**Example Output** (as strings):
```
001-100_A3F7c_draft_my-chapter.md
001-100_A3F7c_notes_my-chapter.md
```

**Display Context**:
- Tree text output: Each path on separate indented line
  ```
  ├─ files: 001-100_A3F7c_draft_my-chapter.md
  └─ files: 001-100_A3F7c_notes_my-chapter.md
  ```
- JSON output: `"files": ["001-100_A3F7c_draft_my-chapter.md", ...]` (as array)

**Edge Cases**:
- No doctypes → no files (consistent with omitting metadata)
- Long paths → display full path without truncation

---

## Subtree Filtering Logic

### Subtree Definition

A **subtree** rooted at node N consists of:
1. The node N itself (root of subtree)
2. All descendants of N (nodes where MP starts with N's MP)

### Filtering Algorithm

**Input**:
- `all_nodes`: List of all nodes in outline (sorted by MP)
- `root_sqid`: SQID of subtree root node

**Output**: List of nodes in the subtree (root + descendants)

**Pseudocode**:
```python
def filter_to_subtree(all_nodes: list[Node], root_sqid: str) -> list[Node]:
    # Find root node
    root_node = find_node_by_sqid(all_nodes, root_sqid)
    if root_node is None:
        raise ValueError(f"SQID {root_sqid} not found")

    # Check if orphaned (special case)
    if is_orphaned(root_node, all_nodes):
        # Return only the node with orphan flag
        return [root_node]  # CLI will add warning

    # Get all descendants
    root_mp = root_node.mp
    descendants = [
        node for node in all_nodes
        if node.mp.segments[:len(root_mp.segments)] == root_mp.segments
        and node.mp != root_mp  # Exclude root itself
    ]

    # Return root + descendants, maintain sort order
    return [root_node] + descendants
```

### Orphan Detection

**Definition**: A node is "orphaned" if it exists in the filesystem but its parent (if any) does not exist in the outline.

**Detection Logic**:
```python
def is_orphaned(node: Node, all_nodes: list[Node]) -> bool:
    # Root nodes (depth 1) cannot be orphaned
    if node.mp.depth == 1:
        return False

    # Check if parent exists
    parent_mp = node.mp.parent()
    parent_exists = any(n.mp == parent_mp for n in all_nodes)

    return not parent_exists
```

**Handling**: When orphaned node is detected:
- Return only that node (no descendants)
- CLI layer adds warning message to stderr
- Exit code 0 (not an error, informational)

---

## Materialized Path Operations

### Parent-Child Relationship

**Parent Calculation** (existing method):
```python
parent_mp = node.mp.parent()  # Returns MaterializedPath | None
# Example: "001-100-050" → "001-100"
```

**Descendant Check**:
```python
def is_descendant(potential_child: Node, ancestor: Node) -> bool:
    child_segments = potential_child.mp.segments
    ancestor_segments = ancestor.mp.segments

    # Child must be deeper than ancestor
    if len(child_segments) <= len(ancestor_segments):
        return False

    # Child's prefix must match ancestor's full path
    return child_segments[:len(ancestor_segments)] == ancestor_segments
```

**Example**:
```
Ancestor: "001-100" (depth 2)
├─ Descendant: "001-100-050" (depth 3) ✓
├─ Descendant: "001-100-200" (depth 3) ✓
│  └─ Descendant: "001-100-200-010" (depth 4) ✓
└─ NOT Descendant: "001-200" (different branch) ✗
```

---

## Display Data Structures

### Tree Text Output Format

**Base Node Line** (existing):
```
[prefix][connector][title] (@[sqid])
```

**With Metadata** (new):
```
[prefix][connector][title] (@[sqid])
[prefix][metadata_connector] doctypes: [comma-separated-list]
[prefix][metadata_connector] files: [relative-path]
[prefix][metadata_connector] files: [relative-path]
...
```

**Connector Characters**:
- Node connectors: `├──` (middle child), `└──` (last child)
- Metadata connectors: `├─` (more metadata), `└─` (last metadata)
- Continuation: `│` (parent has more siblings)

**Example**:
```
Root Chapter (@sqid1)
├── Scene One (@sqid2)
│   ├─ doctypes: draft, notes
│   ├─ files: 001-100_sqid2_draft_scene-one.md
│   └─ files: 001-100_sqid2_notes_scene-one.md
└── Scene Two (@sqid3)
    ├─ doctypes: draft, notes, outline
    ├─ files: 001-200_sqid3_draft_scene-two.md
    ├─ files: 001-200_sqid3_notes_scene-two.md
    └─ files: 001-200_sqid3_outline_scene-two.md
```

### JSON Output Format

**Base Structure** (existing):
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Chapter",
    "slug": "root-chapter",
    "document_types": ["draft", "notes"],
    "children": [...]
  }
]
```

**With Metadata** (new fields - only when flags enabled):
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Chapter",
    "slug": "root-chapter",
    "document_types": ["draft", "notes"],
    "doctypes": ["draft", "notes"],           // NEW: when --show-doctypes
    "files": ["001_sqid1_draft_root.md", ...], // NEW: when --show-files
    "children": [...]
  }
]
```

**Field Presence Rules**:
- `doctypes`: Present only when `--show-doctypes` flag is used AND node has doctypes
- `files`: Present only when `--show-files` flag is used AND node has doctypes
- If node has no doctypes (edge case), omit both fields even with flags enabled

---

## Validation Rules

### Subtree Root SQID

**Valid**:
- Alphanumeric string (per SQID definition)
- Exists in the loaded nodes collection
- May be orphaned (allowed per clarifications)

**Invalid** (raise ValueError):
- Empty string
- Non-existent SQID
- Non-alphanumeric characters

**Error Messages**:
- Invalid format: `"Invalid SQID format: {sqid}"`
- Not found: `"SQID {sqid} not found in outline"`

### Metadata Display

**Doctypes**:
- Source: `node.document_types` (set of strings)
- Display: Sorted alphabetically, comma-separated
- Empty case: Omit metadata line entirely

**Files**:
- Source: Computed from `node.filenames()`
- Display: Relative paths from outline directory
- Empty case: Omit metadata line entirely (consistent with doctypes)

---

## State Transitions

This feature has no state transitions (read-only operation). It does not modify any files or data structures.

---

## Relationships

### Node → Files (1:N)

- One node has N document files (where N = number of document types)
- Relationship is computed, not stored
- Files are named according to pattern: `<mp>_<sqid>_<type>_<slug>.md`

### Node → Node (Parent-Child Hierarchy)

- Existing relationship via materialized path
- No changes to relationship semantics
- Subtree filtering leverages this relationship to find descendants

---

## Examples

### Example 1: Simple Subtree

**Outline**:
```
001 Root (@A1)
  001-100 Chapter 1 (@B2)
    001-100-100 Scene 1A (@C3)
    001-100-200 Scene 1B (@C4)
  001-200 Chapter 2 (@B5)
```

**Command**: `lmk list B2 --show-doctypes`

**Output**:
```
Chapter 1 (@B2)
├─ doctypes: draft, notes
├── Scene 1A (@C3)
│   └─ doctypes: draft, notes
└── Scene 1B (@C4)
    └─ doctypes: draft, notes
```

### Example 2: Leaf Node Subtree

**Command**: `lmk list C3`

**Output**:
```
Scene 1A (@C3)
```

(No children, so only root node displayed)

### Example 3: All Metadata Combined

**Command**: `lmk list B2 --show-doctypes --show-files`

**Output**:
```
Chapter 1 (@B2)
├─ doctypes: draft, notes
├─ files: 001-100_B2_draft_chapter-1.md
├─ files: 001-100_B2_notes_chapter-1.md
├── Scene 1A (@C3)
│   ├─ doctypes: draft, notes
│   ├─ files: 001-100-100_C3_draft_scene-1a.md
│   └─ files: 001-100-100_C3_notes_scene-1a.md
└── Scene 1B (@C4)
    ├─ doctypes: draft, notes
    ├─ files: 001-100-200_C4_draft_scene-1b.md
    └─ files: 001-100-200_C4_notes_scene-1b.md
```

---

## Summary

**No New Entities**: All data exists in current `Node` entity

**No Schema Changes**: No modifications to stored data

**Computed Values**: Doctype strings and file paths are derived at display time

**Filtering Logic**: In-memory filtering using materialized path prefix matching

**Display Enhancements**: Formatters gain optional parameters to show additional metadata
