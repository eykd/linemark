# Linemark CLI Reference

Complete command-line interface documentation for Linemark - a hierarchical Markdown outline manager.

## Table of Contents

- [Overview](#overview)
- [Global Options](#global-options)
- [Commands](#commands)
  - [add](#add) - Create new nodes
  - [compile](#compile) - Concatenate documents
  - [compact](#compact) - Renumber outline
  - [delete](#delete) - Remove nodes
  - [doctor](#doctor) - Validate and repair
  - [list](#list) - Display outline
  - [move](#move) - Reposition nodes
  - [rename](#rename) - Change titles
  - [types](#types) - Manage document types
- [Concepts](#concepts)
- [Examples](#examples)

## Overview

Linemark (`lmk`) is a command-line tool for managing hierarchical outlines of Markdown documents using filename-based organization. Each node in the outline represents a document that can contain multiple document types (draft, notes, etc.).

```bash
lmk [OPTIONS] COMMAND [ARGS]...
```

## Global Options

All commands support these global options:

### `--help`

Display help information for the command.

```bash
lmk --help              # Show main help
lmk add --help          # Show help for add command
lmk types add --help    # Show help for types add subcommand
```

### `--directory DIRECTORY`

Specify the working directory for the outline. Defaults to current directory.

```bash
lmk list --directory /path/to/project
lmk add "Chapter 1" --directory ~/my-novel
```

This option is available for all commands that operate on outline files.

## Commands

### add

Add a new outline node with the specified title.

```bash
lmk add TITLE [OPTIONS]
```

**Arguments:**

- `TITLE` (required): Title of the new node

**Options:**

- `--child-of SQID`: Create as child of specified parent node
- `--sibling-of SQID`: Position relative to specified sibling node
- `--before`: Insert before sibling (requires `--sibling-of`)
- `--after`: Insert after sibling (requires `--sibling-of`)
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Creates a new node with auto-generated SQID identifier
- Creates two files: `<path>-<slug>.draft.md` and `<path>-<slug>.notes.md`
- By default, adds node at root level with next available position
- Automatically positions new nodes with appropriate spacing (100/10/1 depending on tier)

**Examples:**

```bash
# Add a root-level chapter
lmk add "Chapter One"
# Output: Created node 100 (@Gxn7qZp): Chapter One
#         Draft: 100-chapter-one.draft.md
#         Notes: 100-chapter-one.notes.md

# Add a child section under node @Gxn7qZp
lmk add "Section 1.1" --child-of @Gxn7qZp

# Add node before an existing sibling
lmk add "Prologue" --sibling-of @Gxn7qZp --before

# Add node after an existing sibling
lmk add "Epilogue" --sibling-of @Gxn7qZp --after
```

**File Format Created:**

Draft file (`100-chapter-one.draft.md`):
```markdown
---
sqid: Gxn7qZp
title: Chapter One
---

# Chapter One
```

Notes file (`100-chapter-one.notes.md`):
```markdown
---
sqid: Gxn7qZp
title: Chapter One
---

# Notes: Chapter One
```

**Exit Codes:**

- `0`: Success
- `1`: Error (invalid options, node not found, etc.)

---

### compile

Compile all doctype files into a single document.

```bash
lmk compile DOCTYPE [SQID] [OPTIONS]
```

**Arguments:**

- `DOCTYPE` (required): Document type to compile (e.g., `draft`, `notes`)
- `SQID` (optional): Root node SQID to compile from (compiles subtree only)

**Options:**

- `--separator TEXT`: Separator between documents (default: `\n\n---\n\n`)
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Concatenates content from all nodes containing the specified DOCTYPE
- Traverses in hierarchical order (depth-first)
- Outputs to stdout (redirect to file if needed)
- Optionally filters to specific subtree when SQID provided
- Escape sequences in separator are interpreted (e.g., `\n`, `\t`)

**Examples:**

```bash
# Compile all draft files
lmk compile draft

# Compile notes from specific subtree
lmk compile notes @Gxn7qZp

# Use custom separator
lmk compile draft --separator "===PAGE BREAK==="

# Save to file
lmk compile draft > compiled.md

# Compile with no separator
lmk compile draft --separator ""

# Use form feed separator
lmk compile draft --separator "\f"
```

**Output Format:**

```markdown
# Chapter One

Content from first node...

---

# Section 1.1

Content from child node...

---

# Chapter Two

Content from next node...
```

**Exit Codes:**

- `0`: Success (including empty output when no nodes found)
- `1`: Error (doctype not found, node not found, invalid doctype)
- `2`: System error (permission denied, disk full, etc.)

---

### compact

Restore clean, evenly-spaced numbering to the outline.

```bash
lmk compact [SQID] [OPTIONS]
```

**Arguments:**

- `SQID` (optional): Parent node SQID to compact children of

**Options:**

- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Renumbers siblings at specified level with even spacing
- Uses 100s spacing for root level, 10s for second level, 1s for third level
- Preserves hierarchy and relative ordering
- Renames all associated files to match new paths
- If SQID provided, compacts children of that node
- If no SQID provided, compacts root level nodes

**Spacing Tiers:**

- Root level (depth 1): 100, 200, 300, ...
- Second level (depth 2): 100-10, 100-20, 100-30, ...
- Third level (depth 3): 100-10-1, 100-10-2, 100-10-3, ...
- Fourth+ levels: Continue with 1-increments

**Examples:**

```bash
# Compact root-level nodes
# Before: 105, 107, 320, 450
# After:  100, 200, 300, 400
lmk compact

# Compact children of specific node
lmk compact @Gxn7qZp

# Compact after many additions/deletions
lmk compact
# Output: Compacted 8 root-level nodes
```

**Exit Codes:**

- `0`: Success
- `1`: Error (node not found, invalid SQID)

---

### delete

Delete a node from the outline.

```bash
lmk delete SQID [OPTIONS]
```

**Arguments:**

- `SQID` (required): SQID of node to delete (@ prefix optional)

**Options:**

- `-r, --recursive`: Delete node and all descendants
- `-p, --promote`: Delete node but promote children to parent level
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- By default, only deletes leaf nodes (nodes without children)
- Attempting to delete non-leaf node without flags returns error
- `--recursive`: Deletes node and entire subtree
- `--promote`: Deletes node but moves children up to parent level
- All associated files are deleted
- Cannot combine `--recursive` and `--promote`

**Examples:**

```bash
# Delete a leaf node
lmk delete @Gxn7qZp

# Delete node and all descendants
lmk delete @Gxn7qZp --recursive
# Output: Deleted node @Gxn7qZp and 5 descendants

# Delete node but keep children (promote to parent)
lmk delete @Gxn7qZp --promote
# Output: Deleted node @Gxn7qZp (children promoted to parent level)

# SQID format flexible (@ prefix optional)
lmk delete Gxn7qZp
lmk delete @Gxn7qZp  # Both work
```

**Safety:**

- Leaf-only deletion by default prevents accidental data loss
- No confirmation prompt (use with caution)
- Files are permanently deleted (not moved to trash)

**Exit Codes:**

- `0`: Success
- `1`: Error (node not found, has children without flags, invalid options)

---

### doctor

Validate outline integrity and repair common issues.

```bash
lmk doctor [OPTIONS]
```

**Options:**

- `--repair`: Auto-repair common issues
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Validates outline structure and file integrity
- Checks for duplicate SQIDs
- Verifies required files exist (draft and notes)
- Validates file naming matches materialized paths
- Checks YAML frontmatter consistency
- With `--repair`: Automatically fixes common problems

**Validation Checks:**

1. **SQID uniqueness**: No duplicate SQIDs across nodes
2. **Required files**: Draft and notes files exist for each node
3. **Filename consistency**: Files match expected naming pattern
4. **Frontmatter validity**: YAML frontmatter is well-formed
5. **SQID consistency**: Frontmatter SQID matches filename

**Repair Actions:**

- Creates missing draft/notes files with minimal frontmatter
- Does NOT fix duplicate SQIDs (manual intervention required)
- Does NOT rename files (too risky for automation)

**Examples:**

```bash
# Check outline for issues
lmk doctor
# Output: ✗ Outline has integrity issues:
#         • Duplicate SQID found: @Gxn7qZp
#         • Missing notes file: 100-chapter.notes.md
#
#         Run with --repair to auto-fix common issues

# Check and auto-repair issues
lmk doctor --repair
# Output: ✓ Outline is valid
#
#         Repairs performed:
#         • Created missing file: 100-chapter.notes.md
```

**Exit Codes:**

- `0`: Outline is valid (or repaired successfully)
- `1`: Outline has issues that need attention

---

### list

List all nodes in the outline.

```bash
lmk list [OPTIONS]
```

**Options:**

- `--json`: Output in JSON format instead of tree
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Displays outline structure with SQIDs
- Default: Tree format with Unicode box-drawing characters
- JSON format: Nested structure with full node details
- Nodes sorted by materialized path (hierarchical order)

**Examples:**

```bash
# Show tree structure (default)
lmk list
# Output:
# Chapter One (@Gxn7qZp)
# ├── Section 1.1 (@B2k5mNq)
# │   └── Subsection A (@P9x3rTw)
# └── Section 1.2 (@K7j2vLp)
# Chapter Two (@M8h4nDx)

# Show JSON structure
lmk list --json
```

**JSON Output Format:**

```json
[
  {
    "sqid": "Gxn7qZp",
    "mp": "100",
    "title": "Chapter One",
    "slug": "chapter-one",
    "document_types": ["draft", "notes"],
    "children": [
      {
        "sqid": "B2k5mNq",
        "mp": "100-10",
        "title": "Section 1.1",
        "slug": "section-1-1",
        "document_types": ["draft", "notes"],
        "children": []
      }
    ]
  }
]
```

**Exit Codes:**

- `0`: Success (even if no nodes found)

---

### move

Move a node to a new position in the outline.

```bash
lmk move SQID --to TARGET [OPTIONS]
```

**Arguments:**

- `SQID` (required): SQID of node to move (@ prefix optional)

**Options:**

- `--to PATH` (required): Target materialized path (e.g., `200-100`)
- `--before SQID`: Insert before this SQID (future enhancement)
- `--after SQID`: Insert after this SQID (future enhancement)
- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Moves node to new position in outline hierarchy
- All descendants move automatically with updated paths
- SQIDs remain unchanged (permanent identifiers)
- All files renamed to match new materialized paths
- Target path must be valid and available

**Examples:**

```bash
# Move node to root level at position 200
lmk move @Gxn7qZp --to 200
# Output: Moved node @Gxn7qZp to 200
#         All files renamed successfully

# Move node to be child of another node
# From: 100 -> To: 200-300
lmk move @B2k5mNq --to 200-300

# Complex move preserving descendants
# Before: 100-10 with child 100-10-1
# After:  300 with child 300-10
lmk move @B2k5mNq --to 300
```

**File Renaming:**

Moving node from `100-10-chapter.draft.md` to `200-15`:
- `100-10-chapter.draft.md` → `200-15-chapter.draft.md`
- `100-10-chapter.notes.md` → `200-15-chapter.notes.md`
- `100-10-1-section.draft.md` → `200-15-1-section.draft.md`
- etc.

**Exit Codes:**

- `0`: Success
- `1`: Error (node not found, invalid path, target conflict)

---

### rename

Rename a node with a new title.

```bash
lmk rename SQID NEW_TITLE [OPTIONS]
```

**Arguments:**

- `SQID` (required): SQID of node to rename (@ prefix optional)
- `NEW_TITLE` (required): New title for the node

**Options:**

- `--directory DIRECTORY`: Working directory (default: current directory)

**Behavior:**

- Updates title in draft file's frontmatter
- Renames all associated files to use new slug
- SQID remains unchanged (permanent identifier)
- Materialized path remains unchanged (position unchanged)
- Slug regenerated from new title

**Slug Generation:**

Titles are converted to slugs using these rules:
- Lowercase conversion
- Special characters removed
- Spaces converted to hyphens
- Multiple hyphens collapsed to single hyphen

Examples:
- "Chapter One" → "chapter-one"
- "Chapter 2: Hero's Journey" → "chapter-2-heros-journey"
- "Section 1.1" → "section-1-1"

**Examples:**

```bash
# Rename a node
lmk rename @Gxn7qZp "New Chapter Title"
# Output: Renamed node @Gxn7qZp to "New Chapter Title"
#         All files updated successfully

# Works with special characters
lmk rename @Gxn7qZp "Chapter 2: Hero's Journey"

# Files renamed:
# Before: 100-old-title.draft.md
# After:  100-new-chapter-title.draft.md
```

**File Changes:**

1. Frontmatter updated in draft file:
```yaml
---
sqid: Gxn7qZp
title: New Chapter Title
---
```

2. All files renamed:
- `100-old-title.draft.md` → `100-new-chapter-title.draft.md`
- `100-old-title.notes.md` → `100-new-chapter-title.notes.md`
- `100-old-title.characters.md` → `100-new-chapter-title.characters.md`

**Exit Codes:**

- `0`: Success
- `1`: Error (node not found, invalid title, file system error)

---

### types

Manage document types for outline nodes.

```bash
lmk types COMMAND [ARGS]...
```

Document types allow each node to have multiple associated files beyond the required `draft` and `notes`. Examples: `characters`, `worldbuilding`, `outline`, `research`.

#### types list

List all document types for a node.

```bash
lmk types list SQID [OPTIONS]
```

**Arguments:**

- `SQID` (required): Node SQID to list types for

**Options:**

- `--directory DIRECTORY`: Working directory

**Examples:**

```bash
# List types for a node
lmk types list @Gxn7qZp
# Output:
# Document types for @Gxn7qZp:
#   - draft
#   - notes
#   - characters
#   - worldbuilding
```

#### types add

Add a new document type to a node.

```bash
lmk types add DOCTYPE SQID [OPTIONS]
```

**Arguments:**

- `DOCTYPE` (required): Document type to add
- `SQID` (required): Node SQID to add type to

**Options:**

- `--directory DIRECTORY`: Working directory

**Behavior:**

- Creates new empty file with specified document type
- Required types (`draft`, `notes`) cannot be added (already exist)
- Filename format: `<path>-<slug>.<doctype>.md`

**Examples:**

```bash
# Add a characters type to a node
lmk types add characters @Gxn7qZp
# Output: Added type "characters" to node @Gxn7qZp
# Creates: 100-chapter-one.characters.md

# Add worldbuilding type
lmk types add worldbuilding @Gxn7qZp
# Creates: 100-chapter-one.worldbuilding.md
```

**Created File Format:**

```markdown
---
sqid: Gxn7qZp
title: Chapter One
---

# Characters: Chapter One
```

**Exit Codes:**

- `0`: Success
- `1`: Error (type already exists, invalid type name, node not found)

#### types remove

Remove a document type from a node.

```bash
lmk types remove DOCTYPE SQID [OPTIONS]
```

**Arguments:**

- `DOCTYPE` (required): Document type to remove
- `SQID` (required): Node SQID to remove type from

**Options:**

- `--directory DIRECTORY`: Working directory

**Behavior:**

- Deletes file for specified document type
- Required types (`draft`, `notes`) cannot be removed
- File is permanently deleted

**Examples:**

```bash
# Remove a characters type from a node
lmk types remove characters @Gxn7qZp
# Output: Removed type "characters" from node @Gxn7qZp
# Deletes: 100-chapter-one.characters.md

# Attempt to remove required type (error)
lmk types remove draft @Gxn7qZp
# Output: Error: Cannot remove required document type 'draft'
```

**Exit Codes:**

- `0`: Success
- `1`: Error (type not found, required type, node not found)

---

## Concepts

### SQID (Identifier)

Each node has a permanent, unique SQID identifier:

- 7-character alphanumeric string (e.g., `Gxn7qZp`)
- Generated using sqids library
- URL-safe, pronounceable
- Never changes (even when node is moved/renamed)
- Can be specified with or without `@` prefix in commands

### Materialized Path

The hierarchical position of a node:

- Numeric path showing position in tree (e.g., `100-10-1`)
- Root nodes: Single number (100, 200, 300)
- Child nodes: Parent path + hyphen + position (100-10, 100-20)
- Changes when node is moved
- Determines filename prefix

**Path Tiers:**

- **Tier 1** (root): 100s spacing (100, 200, 300, ...)
- **Tier 2** (children): 10s spacing (100-10, 100-20, ...)
- **Tier 3+** (grandchildren): 1s spacing (100-10-1, 100-10-2, ...)

### Slug

URL-friendly version of the title:

- Generated from title
- Lowercase, hyphens, alphanumeric
- Used in filenames
- Changes when title is renamed

### Document Types

Each node can have multiple document files:

- **Required**: `draft` and `notes` (created automatically)
- **Optional**: Any custom type (characters, worldbuilding, etc.)
- Each type is a separate `.md` file
- All share same SQID in frontmatter

### Filename Format

Files follow this naming pattern:

```
<materialized-path>-<slug>.<doctype>.md
```

Examples:
- `100-chapter-one.draft.md`
- `100-chapter-one.notes.md`
- `100-10-section.draft.md`
- `200-15-appendix.characters.md`

### YAML Frontmatter

Each file contains YAML frontmatter:

```yaml
---
sqid: Gxn7qZp
title: Chapter One
---
```

Required fields:
- `sqid`: Node identifier
- `title`: Node title

## Examples

### Complete Workflow

```bash
# Start a new novel
mkdir my-novel
cd my-novel

# Add main chapters
lmk add "Part One"
# Output: Created node 100 (@Gxn7qZp): Part One

lmk add "Part Two"
# Output: Created node 200 (@B2k5mNq): Part Two

# Add sections under Part One
lmk add "Chapter 1" --child-of @Gxn7qZp
# Output: Created node 100-10 (@K7j2vLp): Chapter 1

lmk add "Chapter 2" --child-of @Gxn7qZp
# Output: Created node 100-20 (@M8h4nDx): Chapter 2

# Add subsections
lmk add "Scene 1" --child-of @K7j2vLp
lmk add "Scene 2" --child-of @K7j2vLp

# View structure
lmk list
# Output:
# Part One (@Gxn7qZp)
# ├── Chapter 1 (@K7j2vLp)
# │   ├── Scene 1 (@P9x3rTw)
# │   └── Scene 2 (@Q1y4sTx)
# └── Chapter 2 (@M8h4nDx)
# Part Two (@B2k5mNq)

# Add character notes
lmk types add characters @K7j2vLp

# Compile all draft content
lmk compile draft > manuscript.md

# Move chapter to different part
lmk move @M8h4nDx --to 200-10

# Rename chapter
lmk rename @K7j2vLp "Chapter 1: The Beginning"

# Delete a scene
lmk delete @Q1y4sTx

# Check integrity
lmk doctor --repair

# Clean up numbering
lmk compact
```

### Working with Subtrees

```bash
# Compile only Part One
lmk compile draft @Gxn7qZp > part-one.md

# List Part One structure as JSON
lmk list --json | jq '.[] | select(.sqid == "Gxn7qZp")'

# Compact children of Part One
lmk compact @Gxn7qZp

# Delete entire Part Two and contents
lmk delete @B2k5mNq --recursive
```

### Reorganizing Structure

```bash
# Add prologue before Chapter 1
lmk add "Prologue" --sibling-of @K7j2vLp --before

# Move chapter between parts
lmk move @M8h4nDx --to 200-10

# Delete part but keep chapters (promote)
lmk delete @Gxn7qZp --promote

# Fix messy numbering after many changes
lmk compact
```

### Custom Document Types

```bash
# Add worldbuilding notes
lmk types add worldbuilding @Gxn7qZp

# Add character sheets to multiple nodes
lmk types add characters @K7j2vLp
lmk types add characters @M8h4nDx

# List what types a node has
lmk types list @K7j2vLp

# Compile character notes only
lmk compile characters > all-characters.md

# Remove outdated type
lmk types remove worldbuilding @Gxn7qZp
```

### Batch Operations

```bash
# Compile each top-level node separately
for node in $(lmk list --json | jq -r '.[] | @base64'); do
  sqid=$(echo "$node" | base64 -d | jq -r '.sqid')
  title=$(echo "$node" | base64 -d | jq -r '.title' | tr ' ' '-')
  lmk compile draft "@$sqid" > "output-${title}.md"
done

# Find nodes with specific document type
lmk list --json | jq -r '.[] | select(.document_types | contains(["characters"])) | .sqid'
```

## Exit Codes

All commands use these exit codes:

- `0`: Success
- `1`: Command error (invalid arguments, node not found, validation failure)
- `2`: System error (permission denied, disk full, etc.)

## Error Handling

Common error messages:

```bash
# Node not found
Error: Node with SQID 'Invalid' not found in directory

# Invalid operation
Error: Cannot delete node with children (use --recursive or --promote)

# Doctype not found
Error: No nodes found with doctype 'invalid' in directory

# Missing required option
Error: Missing required option '--to'

# Duplicate SQID (during doctor check)
✗ Outline has integrity issues:
  • Duplicate SQID found: @Gxn7qZp in files:
    - 100-chapter-one.draft.md
    - 200-chapter-two.draft.md
```

## Shell Integration

### Bash Completion

```bash
# Add to ~/.bashrc
eval "$(_LMK_COMPLETE=bash_source lmk)"
```

### Zsh Completion

```bash
# Add to ~/.zshrc
eval "$(_LMK_COMPLETE=zsh_source lmk)"
```

### Fish Completion

```bash
# Add to ~/.config/fish/completions/lmk.fish
_LMK_COMPLETE=fish_source lmk | source
```

## Tips and Best Practices

1. **SQID Aliases**: Consider creating shell aliases for frequently-used SQIDs
   ```bash
   alias chapter1="lmk compile draft @K7j2vLp"
   ```

2. **JSON Queries**: Use `jq` to query outline structure
   ```bash
   lmk list --json | jq '.[] | select(.mp | startswith("100"))'
   ```

3. **Compacting**: Run `lmk compact` after major restructuring to maintain clean numbering

4. **Validation**: Run `lmk doctor` regularly, especially after manual file operations

5. **Backups**: Since operations are destructive, maintain git or backup system
   ```bash
   git init
   git add .
   git commit -m "Checkpoint before major reorganization"
   ```

6. **Custom Separators**: Use form feed (`\f`) for print-friendly separations
   ```bash
   lmk compile draft --separator "\f" > printable.md
   ```

7. **Subtree Operations**: Most commands support working on subtrees via SQID
   ```bash
   lmk compile draft @chapter-sqid
   ```

## See Also

- [README.md](../README.md) - Project overview and quick start
- [Architecture](../src/linemark/) - Hexagonal architecture documentation
- [Contributing](../CONTRIBUTING.md) - Development guidelines
