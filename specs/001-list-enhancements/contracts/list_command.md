# CLI Contract: `lmk list` Command

**Feature**: 001-list-enhancements
**Date**: 2025-11-13
**Version**: 2.0 (extends existing v1.0)

## Command Signature

```bash
lmk list [SQID] [OPTIONS]
```

---

## Arguments

### `SQID` (Optional Positional Argument)

**Type**: String (alphanumeric)

**Description**: SQID of the node to use as the root of the subtree. If provided, only this node and its descendants are displayed.

**Default**: None (display full outline)

**Validation**:
- Must be alphanumeric (letters and digits only)
- Must exist in the outline (raises error if not found)
- May be orphaned (node exists but parent doesn't) - displays with warning

**Examples**:
```bash
lmk list              # Show full outline
lmk list A3F7c        # Show subtree rooted at SQID "A3F7c"
lmk list XyZ9        # Show subtree rooted at SQID "XyZ9"
```

---

## Options

### `--show-doctypes` (Boolean Flag)

**Short Form**: None

**Description**: Display document types for each node. Doctypes are shown on a separate indented line below the node in tree output, or as a `doctypes` field in JSON output.

**Default**: `False` (doctypes not displayed)

**Output Behavior**:
- Tree: Adds indented line(s) below node: `├─ doctypes: draft, notes`
- JSON: Adds `"doctypes": ["draft", "notes"]` field
- If node has no doctypes, metadata line is omitted entirely

**Examples**:
```bash
lmk list --show-doctypes
lmk list A3F7c --show-doctypes
```

---

### `--show-files` (Boolean Flag)

**Short Form**: None

**Description**: Display relative file paths for each node. Paths are shown on separate indented lines below the node in tree output (one per file), or as a `files` array in JSON output.

**Default**: `False` (file paths not displayed)

**Output Behavior**:
- Tree: Adds indented lines below node, one per file:
  ```
  ├─ files: 001-100_sqid_draft_chapter.md
  └─ files: 001-100_sqid_notes_chapter.md
  ```
- JSON: Adds `"files": ["001-100_sqid_draft_chapter.md", ...]` field
- If node has no files (no doctypes), metadata lines are omitted entirely
- Long paths are displayed in full without truncation

**Examples**:
```bash
lmk list --show-files
lmk list A3F7c --show-files
```

---

### `--json` (Boolean Flag)

**Short Form**: None (inherited from existing command)

**Description**: Output nodes as nested JSON structure instead of tree text format.

**Default**: `False` (tree text format)

**Output Behavior**:
- Changes output from tree text to JSON
- Includes `doctypes` field if `--show-doctypes` is set
- Includes `files` field if `--show-files` is set
- Existing fields (`sqid`, `mp`, `title`, `slug`, `document_types`, `children`) are always present

**Examples**:
```bash
lmk list --json
lmk list A3F7c --json
lmk list --show-doctypes --show-files --json
```

---

### `-d, --directory` (Path Option)

**Short Form**: `-d`

**Description**: Working directory containing outline files (inherited from existing command)

**Default**: Current working directory (`.`)

**Examples**:
```bash
lmk list -d /path/to/outline
lmk list --directory ~/my-project
```

---

## Flag Combinations

All flags can be combined freely:

| Combination | Effect |
|-------------|--------|
| `lmk list` | Show full outline as tree (existing behavior) |
| `lmk list --json` | Show full outline as JSON (existing behavior) |
| `lmk list SQID` | Show subtree as tree |
| `lmk list SQID --json` | Show subtree as JSON |
| `lmk list --show-doctypes` | Show full outline with doctypes |
| `lmk list --show-files` | Show full outline with file paths |
| `lmk list --show-doctypes --show-files` | Show full outline with both metadata types |
| `lmk list SQID --show-doctypes --show-files --json` | Show subtree with all metadata as JSON |

---

## Output Formats

### Tree Text Format (Default)

**Base Format** (existing):
```
Root Node (@sqid1)
├── Child Node (@sqid2)
│   └── Grandchild (@sqid3)
└── Another Child (@sqid4)
```

**With `--show-doctypes`**:
```
Root Node (@sqid1)
├─ doctypes: draft, notes
├── Child Node (@sqid2)
│   ├─ doctypes: draft, notes, outline
│   └── Grandchild (@sqid3)
│       └─ doctypes: draft, notes
└── Another Child (@sqid4)
    └─ doctypes: draft
```

**With `--show-files`**:
```
Root Node (@sqid1)
├─ files: 001_sqid1_draft_root.md
├─ files: 001_sqid1_notes_root.md
├── Child Node (@sqid2)
│   ├─ files: 001-100_sqid2_draft_child.md
│   ├─ files: 001-100_sqid2_notes_child.md
│   └─ files: 001-100_sqid2_outline_child.md
│   └── Grandchild (@sqid3)
│       ├─ files: 001-100-100_sqid3_draft_grand.md
│       └─ files: 001-100-100_sqid3_notes_grand.md
└── Another Child (@sqid4)
    └─ files: 001-200_sqid4_draft_another.md
```

**With Both Flags**:
```
Root Node (@sqid1)
├─ doctypes: draft, notes
├─ files: 001_sqid1_draft_root.md
├─ files: 001_sqid1_notes_root.md
└── Child Node (@sqid2)
    ├─ doctypes: draft, notes
    ├─ files: 001-100_sqid2_draft_child.md
    └─ files: 001-100_sqid2_notes_child.md
```

**Formatting Rules**:
- Metadata lines are indented at the same level as the node they describe
- Metadata connectors: `├─` (more metadata below), `└─` (last metadata item)
- Doctypes are sorted alphabetically, comma-separated
- File paths are sorted alphabetically by doctype (via `node.filenames()`)
- Empty metadata is omitted entirely (no lines shown)

---

### JSON Format

**Base Format** (existing):
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Node",
    "slug": "root-node",
    "document_types": ["draft", "notes"],
    "children": [
      {
        "sqid": "sqid2",
        "mp": "001-100",
        "title": "Child Node",
        "slug": "child-node",
        "document_types": ["draft", "notes"],
        "children": []
      }
    ]
  }
]
```

**With `--show-doctypes`**:
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Node",
    "slug": "root-node",
    "document_types": ["draft", "notes"],
    "doctypes": ["draft", "notes"],
    "children": [...]
  }
]
```

**With `--show-files`**:
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Node",
    "slug": "root-node",
    "document_types": ["draft", "notes"],
    "files": [
      "001_sqid1_draft_root.md",
      "001_sqid1_notes_root.md"
    ],
    "children": [...]
  }
]
```

**With Both Flags**:
```json
[
  {
    "sqid": "sqid1",
    "mp": "001",
    "title": "Root Node",
    "slug": "root-node",
    "document_types": ["draft", "notes"],
    "doctypes": ["draft", "notes"],
    "files": [
      "001_sqid1_draft_root.md",
      "001_sqid1_notes_root.md"
    ],
    "children": [...]
  }
]
```

**Field Presence**:
- `doctypes`: Only present when `--show-doctypes` flag is used AND node has doctypes
- `files`: Only present when `--show-files` flag is used AND node has doctypes
- Both fields omitted if node has empty `document_types` set

---

## Exit Codes

| Code | Condition |
|------|-----------|
| 0 | Success (including orphaned node with warning) |
| 1 | Error (invalid SQID, file system error, etc.) |

---

## Standard Streams

### stdout
- Normal output (tree or JSON)
- Used for piping to other commands or files

### stderr
- Error messages
- Warning messages (e.g., "Warning: SQID xyz is orphaned (parent not in outline)")

### Examples

**Success** (exit 0):
```bash
$ lmk list A3F7c
Chapter One (@A3F7c)
├── Scene One (@B8Kd9)
└── Scene Two (@C2Mn3)
```

**Error** (exit 1):
```bash
$ lmk list INVALID
Error: SQID INVALID not found in outline
```

**Warning** (exit 0):
```bash
$ lmk list ORPHAN
Warning: SQID ORPHAN is orphaned (parent not in outline)
Orphaned Node (@ORPHAN)
```

---

## Error Conditions

### Invalid SQID Format

**Condition**: SQID contains non-alphanumeric characters

**Exit Code**: 1

**Error Message** (stderr):
```
Error: Invalid SQID format: 'bad-sqid' (must be alphanumeric)
```

---

### SQID Not Found

**Condition**: SQID doesn't exist in any loaded files

**Exit Code**: 1

**Error Message** (stderr):
```
Error: SQID XyZ9 not found in outline
```

---

### No Nodes Found

**Condition**: Outline directory has no valid markdown files

**Exit Code**: 0 (not an error, empty outline is valid)

**Output** (stderr):
```
No nodes found in outline.
```

---

### File System Error

**Condition**: Cannot read directory or files

**Exit Code**: 1

**Error Message** (stderr):
```
Error: Cannot read outline directory: /path/to/dir
```

---

## Backward Compatibility

### Existing Behavior Preserved

| Command | Behavior | Status |
|---------|----------|--------|
| `lmk list` | Show full outline as tree | ✅ Unchanged |
| `lmk list --json` | Show full outline as JSON | ✅ Unchanged |
| `lmk list -d /path` | Use custom directory | ✅ Unchanged |

### New Behavior (Non-Breaking)

- Optional SQID argument doesn't affect existing usage
- New flags default to False, maintaining current output
- JSON structure extended only when flags are used
- Tree format maintains existing characters and spacing

---

## Performance Expectations

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Full outline (100 nodes) | < 1 second | From command start to first output |
| Subtree filtering | < 2 seconds | Per SC-001 success criterion |
| All flags combined (100 nodes) | < 3 seconds | Per SC-004 success criterion |

---

## Examples Gallery

### Example 1: Basic Subtree

```bash
$ lmk list B8Kd9
Scene One (@B8Kd9)
├── Beat One (@D1Xy7)
└── Beat Two (@E9Pq2)
```

### Example 2: Subtree with Doctypes

```bash
$ lmk list B8Kd9 --show-doctypes
Scene One (@B8Kd9)
├─ doctypes: draft, notes, outline
├── Beat One (@D1Xy7)
│   └─ doctypes: draft, notes
└── Beat Two (@E9Pq2)
    └─ doctypes: draft, notes
```

### Example 3: Everything Combined

```bash
$ lmk list B8Kd9 --show-doctypes --show-files --json
[
  {
    "sqid": "B8Kd9",
    "mp": "001-100",
    "title": "Scene One",
    "slug": "scene-one",
    "document_types": ["draft", "notes", "outline"],
    "doctypes": ["draft", "notes", "outline"],
    "files": [
      "001-100_B8Kd9_draft_scene-one.md",
      "001-100_B8Kd9_notes_scene-one.md",
      "001-100_B8Kd9_outline_scene-one.md"
    ],
    "children": [
      {
        "sqid": "D1Xy7",
        "mp": "001-100-100",
        "title": "Beat One",
        "slug": "beat-one",
        "document_types": ["draft", "notes"],
        "doctypes": ["draft", "notes"],
        "files": [
          "001-100-100_D1Xy7_draft_beat-one.md",
          "001-100-100_D1Xy7_notes_beat-one.md"
        ],
        "children": []
      },
      {
        "sqid": "E9Pq2",
        "mp": "001-100-200",
        "title": "Beat Two",
        "slug": "beat-two",
        "document_types": ["draft", "notes"],
        "doctypes": ["draft", "notes"],
        "files": [
          "001-100-200_E9Pq2_draft_beat-two.md",
          "001-100-200_E9Pq2_notes_beat-two.md"
        ],
        "children": []
      }
    ]
  }
]
```

### Example 4: Leaf Node

```bash
$ lmk list D1Xy7
Beat One (@D1Xy7)
```

(No children, so only root node displayed)

### Example 5: Orphaned Node (Warning)

```bash
$ lmk list ORPHAN
Warning: SQID ORPHAN is orphaned (parent not in outline)
Orphaned Node (@ORPHAN)
```

---

## Type Signatures (Python)

### CLI Function Signature

```python
@lmk.command()
@click.argument('sqid', required=False, type=str)
@click.option('--show-doctypes', is_flag=True, help='Display document types for each node')
@click.option('--show-files', is_flag=True, help='Display file paths for each node')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option('-d', '--directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), default=Path.cwd(), help='Working directory')
def list(
    sqid: str | None,
    show_doctypes: bool,
    show_files: bool,
    output_json: bool,
    directory: Path
) -> None:
    """List nodes in the outline, optionally filtered to a subtree."""
```

### Use Case Signature

```python
class ListOutlineUseCase:
    def execute(
        self,
        directory: Path,
        root_sqid: str | None = None
    ) -> list[Node]:
        """Execute the list outline use case with optional subtree filtering."""
```

### Formatter Signatures

```python
def format_tree(
    nodes: list[Node],
    show_doctypes: bool = False,
    show_files: bool = False,
    directory: Path | None = None
) -> str:
    """Format nodes as tree with optional metadata display."""

def format_json(
    nodes: list[Node],
    show_doctypes: bool = False,
    show_files: bool = False,
    directory: Path | None = None
) -> str:
    """Format nodes as JSON with optional metadata fields."""
```

---

## Testing Contract

### Unit Test Coverage

1. **Argument Parsing**:
   - Optional SQID argument (present/absent)
   - Boolean flags (default False, can be True)
   - All flag combinations

2. **Subtree Filtering**:
   - Valid SQID with children
   - Valid SQID with no children (leaf)
   - Invalid SQID (error)
   - Orphaned SQID (warning)

3. **Metadata Display**:
   - Doctypes only
   - Files only
   - Both combined
   - Neither (backward compatibility)
   - Empty metadata (omit lines)

4. **Output Formats**:
   - Tree text with metadata
   - JSON with metadata fields
   - Field presence rules

### Integration Test Coverage

1. End-to-end command execution
2. Piping JSON output to other commands
3. Performance with 100-node outlines
4. Error handling and exit codes
5. Warning messages to stderr

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Previous | Original `lmk list` command (full outline only) |
| 2.0 | 2025-11-13 | Added SQID argument, --show-doctypes, --show-files flags |
