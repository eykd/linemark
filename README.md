# Linemark

**Hierarchical Markdown outline manager using filename-based organization**

Linemark is a command-line tool for managing structured outlines of Markdown documents. It organizes content hierarchically using materialized paths encoded in filenames, enabling you to build, navigate, and reorganize complex writing projects without nested folders or external databases.

## Overview

Linemark stores your outline structure directly in filenames using a simple but powerful convention. Each node in your outline gets:

- A **materialized path** (like `100-010-001`) that determines its position in the hierarchy
- A **unique stable identifier (SQID)** that never changes, even when moving or renaming
- Multiple **document type files** (draft, notes, characters, etc.) for different kinds of content

This design keeps everything in plain Markdown files with YAML frontmatter, making your content readable by any text editor while providing powerful organizational capabilities through the CLI.

### Key Features

- **Filename-based hierarchy**: Structure encoded in filenames means perfect sorting in any file browser
- **Stable identifiers**: Node SQIDs remain constant across moves and renames for reliable references
- **Multiple document types**: Each node can have draft, notes, and custom document types
- **No hidden state**: Everything visible in filenames and frontmatter - no databases or config files
- **Plain Markdown**: Works with Obsidian, VS Code, and any Markdown-compatible tool
- **Hierarchical operations**: Move entire subtrees, compile by document type, filter by subtree

## Quick Start

### Installation

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

**Requirements**: Python 3.13 or higher

### Create Your First Outline

```bash
# Create a new directory for your project
mkdir my-novel
cd my-novel

# Add a root-level chapter
lmk add "Chapter One"
# Output: Created node 100 (@Gxn7qZp): Chapter One
#         Draft: 100_Gxn7qZp_draft_chapter-one.md
#         Notes: 100_Gxn7qZp_notes_chapter-one.md

# Add a section under the chapter
lmk add "Opening Scene" --child-of @Gxn7qZp

# Add another chapter
lmk add "Chapter Two"

# View your outline
lmk list
# Output:
# Chapter One (@Gxn7qZp)
# └── Opening Scene (@B2k5mNq)
# Chapter Two (@K7j2vLp)
```

### File Structure

After the commands above, your directory contains:

```
my-novel/
├── 100_Gxn7qZp_draft_chapter-one.md
├── 100_Gxn7qZp_notes_chapter-one.md
├── 100-010_B2k5mNq_draft_opening-scene.md
├── 100-010_B2k5mNq_notes_opening-scene.md
├── 200_K7j2vLp_draft_chapter-two.md
└── 200_K7j2vLp_notes_chapter-two.md
```

Each file contains YAML frontmatter:

```markdown
---
sqid: Gxn7qZp
title: Chapter One
---

# Chapter One

Your content here...
```

## Core Concepts

### Materialized Paths

The hierarchical position encoded in the filename:

- `100` - Root-level node (first chapter)
- `100-010` - Child of node 100 (first section)
- `100-010-001` - Child of node 100-010 (first subsection)
- `200` - Root-level node (second chapter)

Materialized paths determine sort order and hierarchy at a glance.

### SQIDs (Stable Identifiers)

Each node gets a unique 7-character identifier like `Gxn7qZp`:

- Generated using the sqids library
- URL-safe and human-readable
- Never changes when you move or rename nodes
- Used for reliable cross-references
- Prefixed with `@` in commands: `@Gxn7qZp`

### Document Types

Each node can have multiple document files:

- **Required**: `draft` (main content) and `notes` (research/ideas)
- **Optional**: Any custom type you create (characters, worldbuilding, outline, etc.)

Example files for one node:
- `100_Gxn7qZp_draft_chapter-one.md`
- `100_Gxn7qZp_notes_chapter-one.md`
- `100_Gxn7qZp_characters_chapter-one.md`

### Filename Format

All files follow this pattern:

```
<materialized-path>_<sqid>_<doctype>_<slug>.md
```

- `<materialized-path>`: Position in hierarchy (e.g., `100-010-001`)
- `<sqid>`: Unique stable identifier (e.g., `Gxn7qZp`)
- `<doctype>`: Document type (e.g., `draft`, `notes`, `characters`)
- `<slug>`: URL-friendly version of title (e.g., `chapter-one`--human-friendly but non-canonical)

## Command Reference

### Managing Nodes

```bash
# Add a root-level node
lmk add "Chapter Title"

# Add a child node
lmk add "Section Title" --child-of @ParentSQID

# Add a sibling node before another
lmk add "Prologue" --sibling-of @ChapterSQID --before

# Add a sibling node after another
lmk add "Epilogue" --sibling-of @ChapterSQID --after
```

### Viewing Structure

```bash
# Show outline as tree
lmk list

# Show specific subtree
lmk list @SQID

# Show with document types
lmk list --show-doctypes

# Show with file paths
lmk list --show-files

# Output as JSON
lmk list --json
```

### Reorganizing

```bash
# Move a node (and all its children)
lmk move @SQID --to 200-010

# Rename a node
lmk rename @SQID "New Title"

# Delete a leaf node
lmk delete @SQID

# Delete node and all descendants
lmk delete @SQID --recursive

# Delete node but promote children
lmk delete @SQID --promote

# Clean up numbering after many changes
lmk compact

# Compact specific subtree
lmk compact @SQID
```

### Document Types

```bash
# List document types for a node
lmk types list @SQID

# Add a custom document type
lmk types add characters @SQID

# Remove a document type
lmk types remove characters @SQID
```

### Compiling

```bash
# Compile all draft files into one document
lmk compile draft > manuscript.md

# Compile notes from a specific subtree
lmk compile notes @SQID > part-one-notes.md

# Use custom separator
lmk compile draft --separator "===PAGE BREAK===" > printable.md
```

### Maintenance

```bash
# Validate outline integrity
lmk doctor

# Auto-repair common issues
lmk doctor --repair
```

### Global Options

All commands support:

- `--directory PATH` - Operate on a different directory (default: current directory)
- `--help` - Show command-specific help

## Use Cases

### Novel Writing

```bash
mkdir my-novel
cd my-novel

# Structure
lmk add "Part One"
lmk add "Chapter 1: The Beginning" --child-of @PartOneSQID
lmk add "Chapter 2: The Journey" --child-of @PartOneSQID

# Add character sheets
lmk types add characters @Chapter1SQID
lmk types add characters @Chapter2SQID

# Compile manuscript
lmk compile draft > manuscript.md

# Reorganize later
lmk move @Chapter2SQID --to 300  # Move to different part
```

### Documentation Projects

```bash
mkdir api-docs
cd api-docs

# Structure
lmk add "Getting Started"
lmk add "API Reference"
lmk add "REST Endpoints" --child-of @APISQID
lmk add "Authentication" --child-of @APISQID

# Add examples as custom doctype
lmk types add examples @EndpointsSQID

# Compile for publication
lmk compile draft --separator "\n\n" > combined-docs.md
```

### Research Projects

```bash
mkdir research
cd research

# Outline
lmk add "Literature Review"
lmk add "Methodology"
lmk add "Results"

# Each section gets draft + notes automatically
# Add custom doctypes for specific needs
lmk types add citations @LitReviewSQID
lmk types add data @ResultsSQID
```

## Architecture

Linemark follows hexagonal (ports and adapters) architecture:

- **Domain**: Core business logic (materialized paths, SQIDs, node operations)
- **Ports**: Interfaces for external dependencies (filesystem, ID generation, etc.)
- **Adapters**: Concrete implementations (FileSystemAdapter, SQIDGeneratorAdapter, etc.)
- **Use Cases**: Application logic orchestrating domain operations
- **CLI**: Command-line interface layer using Click

This design keeps the core logic independent of frameworks and external dependencies.

## Technology Stack

- **Python 3.13+** - Modern Python with full type hints
- **Click** - Command-line interface framework
- **sqids** - Short unique identifier generation
- **PyYAML** - YAML frontmatter parsing
- **python-slugify** - Title-to-slug conversion
- **Pydantic** - Data validation and settings

## Development

### Setup

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

The project maintains comprehensive test coverage:

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test complete workflows end-to-end
- **Contract tests**: Verify API interfaces and port implementations

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=linemark --cov-report=html
```

### Code Quality

The project enforces strict quality standards:

- 100% type coverage with mypy
- PEP 8 compliance with 120-character line limit
- Comprehensive test coverage
- Hexagonal architecture with clear separation of concerns

## Integration with Other Tools

### Git

Linemark files are designed for version control:

```bash
# Initialize git in your project
cd my-novel
git init
git add .
git commit -m "Initial outline"

# All changes are plain text diffs
lmk move @SQID --to 200
git diff  # Shows file renames clearly
```

### Obsidian

Linemark files work as Obsidian notes:

- Each file appears as a separate note
- YAML frontmatter is preserved
- Natural hierarchy in file browser when sorted
- Use Obsidian for editing, linemark for restructuring

### Text Editors

Any text editor works:

- VS Code: Use the built-in Markdown preview
- Vim: Full editing capability with Markdown plugins
- Emacs: org-mode-like structure with Markdown syntax

## Best Practices

1. **Use version control**: Initialize git to track changes and enable rollback
2. **Run compact periodically**: After major reorganizations, run `lmk compact` to restore clean numbering
3. **Validate with doctor**: Run `lmk doctor` before committing to catch issues
4. **Use descriptive titles**: Titles become slugs, so make them meaningful
5. **Leverage subtree operations**: Use SQID filtering for focused work on sections
6. **Custom document types**: Create document types that match your workflow
7. **Compile by document type**: Use `lmk compile` to extract specific views of your content

## FAQ

**Q: Can I edit files manually?**
A: Yes! All files are plain Markdown. Just preserve the YAML frontmatter and run `lmk doctor` to verify integrity.

**Q: What happens to SQIDs when I move nodes?**
A: SQIDs never change. They're stable identifiers for permanent references.

**Q: Can I use nested folders?**
A: No. Linemark uses a flat directory structure with hierarchy encoded in filenames.

**Q: How do I reference another node?**
A: Use the SQID in your content: "See @Gxn7qZp for details". The SQID never changes.

**Q: What if two processes modify the same outline?**
A: Linemark uses optimistic concurrency. Use git for conflict resolution if needed.

**Q: Can I import existing Markdown files?**
A: Not automatically in the MVP. You'll need to create nodes and copy content manually.

## Documentation

- [CLI Reference](docs/CLI.md) - Complete command documentation
- [Specification](specs/001-linemark-cli-mvp/spec.md) - Detailed feature specification
- [Architecture](src/linemark/) - Code organization and design

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests and type checking pass
5. Submit a pull request

## License

[MIT License](LICENSE.md)

## Support

- File issues on GitHub
- Check [CLI Reference](docs/CLI.md) for detailed command help
- Review test cases for usage examples
