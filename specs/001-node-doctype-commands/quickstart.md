# Quickstart Guide: Node and Document Type Operations

**Feature**: 001-node-doctype-commands
**Date**: 2025-11-15

## Overview

This guide shows you how to use the three new linemark commands for working with individual nodes and document types.

## Commands

### 1. `lmk types read` - Read Document Type Content

Read the body content of a specific document type for a node (excluding YAML frontmatter).

**Basic Usage**:
```bash
# Read the notes for a specific node
lmk types read notes @ABC123

# Read characters doctype
lmk types read characters @XYZ789

# Specify a different directory
lmk types read notes @ABC123 --directory /path/to/outline
```

**Output**:
```
The body content is displayed to stdout.

Multiple paragraphs are preserved exactly as stored.
```

**Common Use Cases**:
- View content without opening an editor
- Extract specific doctype content for processing
- Pipe to other tools: `lmk types read notes @ABC123 | grep "TODO"`

**Error Handling**:
- If node doesn't exist: `Error: Node @ABC123 not found`
- If doctype doesn't exist: `Error: Document type 'notes' not found for node @ABC123`

---

### 2. `lmk types write` - Write Document Type Content

Write new body content to a document type file from stdin. Preserves existing YAML frontmatter.

**Basic Usage**:
```bash
# Write new content from echo
echo "New content here" | lmk types write notes @ABC123

# Write multiline content using heredoc
lmk types write notes @ABC123 << EOF
First paragraph.

Second paragraph with **markdown**.
EOF

# Pipe from file
cat draft.md | lmk types write notes @ABC123

# Pipe from another command
lmk types read notes @ABC123 | sed 's/old/new/g' | lmk types write notes @ABC123
```

**Behavior**:
- **Existing file**: Preserves YAML frontmatter, replaces body only
- **New file**: Creates minimal frontmatter (sqid, doctype) + body
- **Empty stdin**: Creates/updates with empty body (Unix tool convention)
- **Atomic write**: Uses temp file + rename (original intact if fails)

**Common Use Cases**:
- Bulk content updates via scripting
- Content transformation pipelines
- Automated content generation

**Error Handling**:
- If node doesn't exist: `Error: Node @ABC123 not found`
- If disk full: `Error: Disk full, cannot write file`
- If permission denied: `Error: Permission denied writing file`

---

### 3. `lmk search` - Search Across Nodes

Search for regex or literal patterns across the outline. Results ordered by outline position.

**Basic Usage**:
```bash
# Search entire outline (case-insensitive by default)
lmk search "error"

# Search with regex pattern
lmk search "chapter [0-9]+"

# Case-sensitive search
lmk search --case-sensitive "Error"

# Literal search (treat * as literal, not regex)
lmk search --literal "foo*"

# Multiline search (pattern can span lines)
lmk search --multiline "start.*end"
```

**Filtering**:
```bash
# Search within a subtree
lmk search @ABC123 "pattern"

# Filter by document type(s)
lmk search --doctype=notes "pattern"
lmk search --doctype=notes --doctype=characters "pattern"

# Combine subtree and doctype filters
lmk search --doctype=notes @ABC123 "pattern"
```

**Output Formats**:
```bash
# Default plaintext output
lmk search "foo"
# Output:
# @ABC123: 100-200-300_ABC123_notes_chapter-1.md
# 42: This line contains foo in it
# @DEF456: 100-200-400_DEF456_notes_chapter-2.md
# 7: Another line with foo

# JSON output (for programmatic use)
lmk search --json "foo"
# Output:
# [
#   {
#     "sqid": "ABC123",
#     "filename": "100-200-300_ABC123_notes_chapter-1.md",
#     "line_number": 42,
#     "content": "This line contains foo in it"
#   },
#   {
#     "sqid": "DEF456",
#     "filename": "100-200-400_DEF456_notes_chapter-2.md",
#     "line_number": 7,
#     "content": "Another line with foo"
#   }
# ]
```

**Common Use Cases**:
- Find all TODOs: `lmk search "TODO"`
- Find character mentions: `lmk search "Alice"`
- Find chapter references: `lmk search "chapter [0-9]+"`
- Extract structured data: `lmk search --json "^#" | jq .`

**Error Handling**:
- If invalid regex: `Error: Invalid regex pattern: [details]`
- If subtree not found: `Error: Node @ABC123 not found`

---

## Workflow Examples

### Example 1: Read-Edit-Write Workflow

Extract content, edit with external tool, write back:

```bash
# Read current content
lmk types read notes @ABC123 > temp.md

# Edit in your favorite editor
$EDITOR temp.md

# Write modified content back
cat temp.md | lmk types write notes @ABC123
```

### Example 2: Bulk Find and Replace

Find and replace text across multiple nodes:

```bash
# Find all matching nodes
lmk search "old phrase" --json | jq -r '.[] | .sqid' | sort -u > sqids.txt

# For each matching SQID, read-replace-write
while read sqid; do
    lmk types read notes @$sqid | \
        sed 's/old phrase/new phrase/g' | \
        lmk types write notes @$sqid
done < sqids.txt
```

### Example 3: Generate Content Report

Create a report of all character descriptions:

```bash
# Search for character sections
lmk search --doctype=characters "^#" --json | \
    jq -r '.[] | "\(.sqid): \(.content)"' > characters-report.txt
```

### Example 4: Validate Content

Check for broken references or TODO items:

```bash
# Find all TODO items across outline
lmk search "TODO:" > todos.txt

# Check for broken links
lmk search "\[.*\]\(.*\)" --json | \
    jq -r '.[] | .content' | \
    # Further processing to validate links...
```

---

## Options Reference

### Common Options (all commands)

- `--directory DIRECTORY` - Working directory (default: current directory)
- `--help` - Show help message with examples

### `lmk types read` Options

```
Usage: lmk types read [OPTIONS] DOC_TYPE @SQID

Arguments:
  DOC_TYPE  Document type name (e.g., notes, characters)
  @SQID     Node identifier with @ prefix

Options:
  --directory DIRECTORY  Working directory (default: current directory)
  --help                 Show this message and exit
```

### `lmk types write` Options

```
Usage: lmk types write [OPTIONS] DOC_TYPE @SQID

Arguments:
  DOC_TYPE  Document type name (e.g., notes, characters)
  @SQID     Node identifier with @ prefix

Options:
  --directory DIRECTORY  Working directory (default: current directory)
  --help                 Show this message and exit

Reads content from stdin.
```

### `lmk search` Options

```
Usage: lmk search [OPTIONS] [SQID] PATTERN

Arguments:
  SQID     Optional subtree root (e.g., @ABC123)
  PATTERN  Search pattern (regex by default)

Options:
  --doctype TEXT         Limit to document type(s), repeatable
  --case-sensitive       Enable case-sensitive matching
  --multiline            Allow patterns to match across lines
  --literal              Treat PATTERN as literal, not regex
  --json                 Output in JSON format
  --directory DIRECTORY  Working directory (default: current directory)
  --help                 Show this message and exit
```

---

## Tips and Best Practices

### Performance

- **Search large outlines**: Use `--doctype` to filter and speed up searches
- **Regex optimization**: Simple patterns are faster; avoid greedy quantifiers when possible
- **Piping**: Commands are designed for Unix pipelines; combine them freely

### Safety

- **Atomic writes**: `types write` uses atomic operations; safe to interrupt
- **Backup before bulk changes**: Use git or create backups before scripting mass updates
- **Test regex patterns**: Try `lmk search --json "pattern" | jq length` to see match count first

### Automation

- **Scripting**: All commands are script-friendly (exit codes, stderr for errors)
- **JSON parsing**: Use `jq` for parsing JSON output
- **Error handling**: Check exit codes in scripts: `if lmk types read notes @ABC123; then ...`

### SQID Format

- **With @ prefix**: CLI accepts `@ABC123` format
- **Without prefix**: Internally uses `ABC123` (@ is stripped)
- **Consistency**: Use @ in CLI commands for clarity

---

## Next Steps

- **Implementation**: See `tasks.md` for development tasks
- **API Details**: See `contracts/` for port protocol specifications
- **Data Model**: See `data-model.md` for entity definitions
- **Technical Decisions**: See `research.md` for technology choices

---

## Help and Documentation

For detailed help on any command:

```bash
lmk types read --help
lmk types write --help
lmk search --help
```

For general linemark help:

```bash
lmk --help
```
