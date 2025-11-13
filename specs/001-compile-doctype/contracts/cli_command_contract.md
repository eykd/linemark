# CLI Command Contract: lmk compile

**Feature**: `001-compile-doctype`
**Component**: `linemark.cli.main.compile`
**Date**: 2025-11-13

## Purpose

Provide command-line interface for compiling doctype files from the forest outline.

## Command Signature

```bash
lmk compile DOCTYPE [SQID] [OPTIONS]
```

### Arguments

**DOCTYPE** (required, positional)
- **Type**: String
- **Description**: Name of doctype to compile (e.g., "draft", "notes", "summary")
- **Validation**: Must be non-empty, no path separators
- **Examples**: `draft`, `notes`, `summary`

**SQID** (optional, positional)
- **Type**: String
- **Description**: SQID of subtree root (with or without @ prefix)
- **Validation**: Valid SQID format (alphanumeric)
- **Examples**: `Gxn7qZp`, `@Gxn7qZp`
- **Behavior**: If provided, compiles only that subtree; if omitted, compiles entire forest

### Options

**--separator TEXT**
- **Type**: String
- **Default**: `'\n\n---\n\n'` (two newlines, three hyphens, two newlines)
- **Description**: Separator to insert between concatenated documents
- **Escape Sequences**: Interpreted (e.g., `\n` → newline, `\t` → tab)
- **Examples**:
  - `--separator "===PAGE BREAK==="`
  - `--separator "\n\n***\n\n"`
  - `--separator ""`  (empty separator)

**--directory PATH**
- **Type**: Path
- **Default**: Current working directory (`.`)
- **Description**: Directory containing the forest outline
- **Validation**: Must exist and be readable
- **Examples**:
  - `--directory /path/to/forest`
  - `--directory ~/Documents/project`

## Output Specification

### Standard Output (stdout)

**Success Cases**:
```
[Compiled content with separators]
```

- **Format**: Plain text UTF-8
- **Content**: Concatenated doctype files with configured separators
- **Empty Case**: Empty string (no output) if no content found
- **Exit Code**: 0

**Example Output**:
```
Chapter One: The Beginning

This is the first chapter...

---

Chapter One Point One: The Deep Dive

This section explores...

---

Chapter Two: The Middle

Continuing the story...
```

### Standard Error (stderr)

**Error Cases**:
- Invalid doctype name
- Doctype not found in forest/subtree
- Invalid SQID
- SQID not found
- Invalid directory path
- Directory not readable
- File system errors

**Error Format**:
```
Error: [Clear description of what went wrong]
```

**Examples**:
```
Error: Doctype 'draf' not found in forest. Check doctype name and ensure at least one node has this file.
Error: Node with SQID 'invalid' not found
Error: Directory '/nonexistent' does not exist
```

### Exit Codes

| Code | Meaning | Trigger |
|------|---------|---------|
| 0 | Success | Compilation completed (even if empty result) |
| 1 | User Error | Invalid arguments, doctype not found, SQID not found |
| 2 | System Error | File system errors, permission denied, I/O failures |

## Command Behavior Contract

### Scenario 1: Basic Compilation

```bash
$ lmk compile draft
Chapter One

This is chapter one content.

---

Chapter Two

This is chapter two content.
```

**Exit**: 0

### Scenario 2: Subtree Compilation

```bash
$ lmk compile draft @Gxn7qZp
Section 1.1

Content from subtree only.

---

Section 1.1.1

Nested content.
```

**Exit**: 0

### Scenario 3: Custom Separator

```bash
$ lmk compile notes --separator "\n\n***\n\n"
Note one

***

Note two
```

**Exit**: 0

### Scenario 4: Empty Separator

```bash
$ lmk compile summary --separator ""
Summary OneSummary TwoSummary Three
```

**Exit**: 0

### Scenario 5: No Content Found

```bash
$ lmk compile draft
[no output]
```

**Exit**: 0
**Behavior**: Silent success - empty string to stdout

### Scenario 6: Doctype Not Found

```bash
$ lmk compile invalidtype
Error: Doctype 'invalidtype' not found in forest. Check doctype name and ensure at least one node has this file.
```

**Exit**: 1
**Behavior**: Error to stderr, no output to stdout

### Scenario 7: SQID Not Found

```bash
$ lmk compile draft @invalid
Error: Node with SQID 'invalid' not found
```

**Exit**: 1

### Scenario 8: Custom Directory

```bash
$ lmk compile draft --directory ~/projects/mybook
[compiled content from ~/projects/mybook forest]
```

**Exit**: 0

### Scenario 9: Invalid Directory

```bash
$ lmk compile draft --directory /nonexistent
Error: Directory '/nonexistent' does not exist
```

**Exit**: 1

## Integration with Shell

### Piping Support

```bash
# Pipe to file
$ lmk compile draft > compiled_draft.md

# Pipe to pager
$ lmk compile draft | less

# Pipe to word count
$ lmk compile draft | wc -w

# Pipe to another command
$ lmk compile draft | pandoc -f markdown -t pdf -o output.pdf
```

### Exit Code Checking

```bash
# Shell scripts
if lmk compile draft > output.md; then
    echo "Compilation successful"
else
    echo "Compilation failed"
fi

# Make-style workflows
compile-all:
    lmk compile draft > draft.md
    lmk compile notes > notes.md
    lmk compile summary > summary.md
```

### Escape Sequence Handling in Shell

```bash
# Single quotes preserve literal backslashes
$ lmk compile draft --separator '\n---\n'

# Double quotes may require escaping
$ lmk compile draft --separator "\\n---\\n"

# Using $'...' syntax (bash/zsh)
$ lmk compile draft --separator $'\n---\n'
```

## Error Message Quality

All error messages MUST:
1. Clearly state what went wrong
2. Provide actionable guidance where possible
3. Include relevant context (file names, SQID values, etc.)
4. Be concise (preferably single line)
5. Avoid technical jargon where possible

**Good Examples**:
- `Error: Doctype 'draf' not found in forest. Check doctype name and ensure at least one node has this file.`
- `Error: Node with SQID 'abc123' not found`
- `Error: Cannot read directory '/restricted': Permission denied`

**Bad Examples** (avoid these):
- `Error: Exception in use case` (too vague)
- `Error: FileNotFoundError: [Errno 2] No such file or directory: '/path'` (too technical)
- `Error` (no context)

## Help Text

```bash
$ lmk compile --help
Usage: lmk compile [OPTIONS] DOCTYPE [SQID]

  Compile all doctype files into a single document.

  Concatenates content from all nodes containing the specified DOCTYPE,
  traversing in hierarchical order (depth-first). Optionally filter to a
  specific subtree by providing a SQID.

Arguments:
  DOCTYPE  Name of doctype to compile (e.g., 'draft', 'notes')  [required]
  SQID     SQID of subtree root (optional, @ prefix allowed)

Options:
  --separator TEXT     Separator between documents [default: '\n\n---\n\n']
  --directory PATH     Working directory  [default: current directory]
  --help               Show this message and exit

Examples:
  # Compile all draft files
  lmk compile draft

  # Compile notes from specific subtree
  lmk compile notes @Gxn7qZp

  # Use custom separator
  lmk compile draft --separator "===PAGE BREAK==="

  # Save to file
  lmk compile draft > compiled.md
```

## Implementation Requirements

1. **Click Framework**: Use Click decorators and conventions
2. **Error Handling**: Catch use case exceptions, convert to appropriate CLI errors
3. **Output**: Write compiled content directly to stdout (no buffering issues)
4. **Logging**: Only errors to stderr; no info/debug logging unless --verbose (future)
5. **SQID Prefix**: Strip @ prefix if user provides it (e.g., "@Gxn7qZp" → "Gxn7qZp")
6. **Exit Codes**: Use appropriate exit codes for error types
7. **Help Text**: Provide clear, helpful documentation in --help output

## Testing Requirements

Contract tests MUST verify:
- Correct argument parsing
- Proper error handling and exit codes
- Output routing (stdout vs stderr)
- SQID prefix stripping
- Integration with use case layer
- Help text accuracy
