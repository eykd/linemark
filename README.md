# Linemark CLI Writing Project Manager

Linemark is a command-line tool for planning, organizing, and writing stories using a hierarchical document structure. It provides a clean, file-based approach to managing complex writing projects with structured content nodes, notes, and flexible organization.

## Overview

Linemark helps writers organize their work by breaking down documents into a hierarchical structure of nodes stored in plain Markdown files. Each node contains main content, metadata, and optional notes. The project uses a "binder" approach where the overall structure is maintained in a special `_binder.md` file, while individual content pieces are stored in separate files.

Key features:
- **File-based storage**: All content in plain Markdown files
- **Hierarchical organization**: Tree structure of content nodes
- **Editor integration**: Launch your preferred editor for content editing
- **Atomic operations**: Safe file operations that preserve existing content
- **Audit capabilities**: Check project integrity and consistency

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/linemark.git
cd linemark

# Install with uv (recommended)
uv sync
uv run lmk --help

# Or install with pip
pip install -e .
lmk --help
```

### System Requirements

- Python 3.13 or higher
- Your preferred text editor (set via EDITOR environment variable)

## Quick Start

### 1. Initialize a New Project

```bash
# Create a new writing project
mkdir my-novel
cd my-novel
lmk init --title "My Great Novel"
```


### 2. Add Content Nodes

```bash
# Add top-level chapters
lmk add "Part 1: The Beginning"
lmk add "Chapter 1: Origins" --parent 01234567

# The output shows the generated UUIDv7 identifier:
# Added "Part 1: The Beginning" (01234567)
# Created files: 01234567.md, 01234567.notes.md
```

### 3. View Project Structure

```bash
lmk structure

# Output:
# Project Structure:
# ├─ Part 1: The Beginning (01234567)
# │  └─ Chapter 1: Origins (89abcdef)
```

### 4. Edit Content

```bash
# Edit the main content
lmk edit 89abcdef --part draft

# Edit notes
lmk edit 89abcdef --part notes

# Edit synopsis (metadata)
lmk edit 89abcdef --part synopsis
```

### 5. Create Freeform Content

```bash
# Quick writing for ideas outside the main structure
lmk write "Character development ideas"

# Creates: 20250920T1530_01234567-89ab-cdef-0123-456789abcdef.md
```

## Command Reference

### Project Management

- `lmk init --title TITLE [--path PATH]` - Initialize new project
- `lmk audit [--fix]` - Check project integrity

### Content Management

- `lmk add TITLE [--parent ID] [--position INDEX]` - Add new node
- `lmk edit NODE_ID --part {draft|notes|synopsis}` - Edit content
- `lmk materialize TITLE [--parent ID]` - Convert placeholder to node
- `lmk move NODE_ID [--parent ID] [--position INDEX]` - Reorganize hierarchy
- `lmk remove NODE_ID [--delete-files] [--force]` - Remove node

### Viewing and Organization

- `lmk structure [--format {tree|json}]` - Display project hierarchy
- `lmk write [TITLE]` - Create timestamped freeform file

## File Structure

Linemark organizes projects with this structure:

```
my-novel/
├── _binder.md                    # Project structure (managed content)
├── 01234567.md                   # Node content file
├── 01234567.notes.md             # Node notes file
├── 89abcdef.md                   # Another node
├── 89abcdef.notes.md             # Its notes
└── 20250920T1530_*.md            # Freeform writing files
```

### Binder File Format

The `_binder.md` file contains your project structure between managed markers:

```markdown
# My Novel

Your project description and notes.

<!-- lmk:begin-binder -->
- [Part 1: The Beginning](01234567.md)
  - [Chapter 1: Origins](89abcdef.md)
  - [Future Chapter]()
<!-- lmk:end-binder -->

Additional content is preserved outside the managed section.
```

### Node File Format

Each node consists of two files with YAML frontmatter:

**Content file (01234567.md)**:
```markdown
---
id: 01234567
title: "Part 1: The Beginning"
synopsis: |
  Opening section that establishes
  the world and main characters
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Part 1: The Beginning

Your story content goes here...
```

**Notes file (01234567.notes.md)**:
```markdown
---
id: 01234567
title: "Part 1: The Beginning"
created: 2025-09-20T15:30:00Z
updated: 2025-09-20T15:30:00Z
---

# Notes for Part 1

Research, character details, plot notes...
```

## Configuration

### Editor Setup

Set your preferred editor via environment variable:

```bash
export EDITOR="code --wait"    # VS Code
export EDITOR="vim"            # Vim
export EDITOR="nano"           # Nano
```

### Integration with Other Tools

Linemark files are designed to work well with:

- **Git**: All files are plain text and diff-friendly
- **Obsidian**: Files appear as individual notes with preserved frontmatter
- **Any text editor**: Standard Markdown with YAML frontmatter
- **Static site generators**: Compatible with Jekyll, Hugo, etc.

## Architecture

Linemark uses hexagonal (ports and adapters) architecture:

- **Domain**: Core business logic (nodes, binders, identifiers)
- **Ports**: Interfaces for external dependencies
- **Adapters**: File system, editor, console implementations
- **Use Cases**: Application logic orchestrating the domain
- **CLI**: Command-line interface layer

This design ensures the core logic is independent of file systems, editors, or CLI frameworks.

## Development

### Tech Stack

- **Python 3.13+** with type hints
- **Typer** for CLI framework
- **PyYAML** for frontmatter parsing
- **pytest** for testing with 100% coverage
- **ruff** for formatting and linting
- **mypy** for type checking

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Type checking
uv run mypy src/

# Linting and formatting
uv run ruff check src/
uv run ruff format src/
```

### Testing

The project uses comprehensive testing:

- **Contract tests**: Verify API interfaces
- **Unit tests**: Test individual components
- **Integration tests**: Test complete workflows
- **Performance tests**: Ensure scalability

Run specific test suites:

```bash
uv run pytest tests/contract/     # Contract tests
uv run pytest tests/unit/        # Unit tests
uv run pytest tests/integration/ # Integration tests
uv run pytest tests/performance/ # Performance tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass and coverage remains 100%
5. Submit a pull request

## License

[MIT License](LICENSE.md)

## Support

For issues, feature requests, or questions:
- File an issue on GitHub
- Check existing documentation in the `specs/` directory
- Review test cases for usage examples
