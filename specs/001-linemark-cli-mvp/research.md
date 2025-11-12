# Research: Linemark Technical Decisions

**Feature**: Linemark - Hierarchical Markdown Outline Manager
**Date**: 2025-11-12
**Phase**: 0 (Pre-implementation Research)

## Overview

This document records technical research and decisions made during Phase 0 planning to resolve unknowns and validate technology choices for the Linemark MVP.

---

## R1: SQID Library Selection & Usage

### Decision
Use **sqids-python 0.5.0+** for generating stable, short, URL-safe identifiers.

### Rationale
- **Canonical Python implementation**: Official sqids library for Python (https://sqids.org/python)
- **Collision resistance**: Base-62 encoding of monotonically increasing integers ensures uniqueness
- **Short & readable**: Generates compact IDs (e.g., "A3F7c", "B9x2k") suitable for filenames
- **No configuration needed**: Zero-config setup aligns with MVP simplicity requirement (FR-036)
- **Deterministic**: Same input integer always produces same SQID (testable, predictable)

### Alternatives Considered
- **UUIDv7**: Constitution specifies UUIDv7, but it generates 36-character IDs (too long for filenames). SQIDs provide shorter identifiers while maintaining uniqueness through monotonic counter.
- **Short UUID libraries**: Add unnecessary complexity for encoding/decoding when sqids is purpose-built.
- **Manual base-62 encoding**: Reinventing the wheel; sqids is battle-tested and maintained.

### Implementation Notes
```python
from sqids import Sqids

sqids = Sqids(min_length=5)  # Minimum 5 characters for readability
sqid = sqids.encode([counter])  # Encode monotonic counter
```

**Counter Derivation** (per clarification): Scan all existing `.md` files matching pattern, decode SQIDs back to integers, find max, use max+1 for next ID.

---

## R2: Click vs Typer for CLI Framework

### Decision
Use **Click 8.1.8+** for CLI implementation.

### Rationale
- **Constitution compliance**: Both Click and Typer listed in constitution (§ Technology Standards)
- **Maturity & stability**: Click is battle-tested with 10+ years of production use
- **Explicit control**: Decorator-based approach gives fine-grained control over argument parsing, validation, and error messages
- **Wide adoption**: Extensive documentation, community support, integration examples
- **No magic**: Behavior is explicit and predictable (important for fail-fast error handling per FR-042)

### Alternatives Considered
- **Typer 0.12.0+**: Modern, type-hint based CLI framework. Rejected because:
  - Less explicit control over error messages and validation
  - Adds pydantic dependency for CLI layer (already using for domain validation)
  - Click's decorator syntax clearer for command groups (`lmk add`, `lmk move`, etc.)

### Implementation Notes
```python
import click

@click.group()
def lmk():
    """Linemark - Hierarchical Markdown Outline Manager"""
    pass

@lmk.command()
@click.argument('title')
@click.option('--child-of', help='Parent node SQID or MP')
@click.option('--directory', type=click.Path(), help='Working directory')
def add(title, child_of, directory):
    """Add a new outline node"""
    # Delegate to AddNode use case
```

---

## R3: Materialized Path Calculation Algorithms

### Decision
Implement **tiered numbering with interval halving** for insertions and **uniform redistribution** for compaction.

### Rationale
- **Insertion algorithm**: When adding sibling before/after, calculate midpoint between neighbors using integer division. If midpoint equals neighbor (no space), error with guidance to compact (per FR-040).
- **Compact algorithm**: For N siblings, renumber as: 100, 200, 300, ... for top tier; 010, 020, 030, ... for mid tier; 001, 002, 003, ... for fine tier (per FR-023).
- **Depth handling**: Each level in hierarchy adds one segment (001-100-050 = depth 3).

### Alternatives Considered
- **Fractional paths** (e.g., "001.5"): Rejected - breaks three-digit invariant and lexicographic sorting.
- **Auto-extend to 4 digits**: Rejected - breaks existing parsers and SC-005 (alphabetical sort guarantee).
- **Random spacing**: Rejected - unpredictable, hard to test, confusing for users.

### Implementation Notes
**Insertion**:
```python
def find_insertion_position(siblings, before_sqid):
    neighbors = get_adjacent_siblings(siblings, before_sqid)
    left_mp, right_mp = neighbors
    midpoint = (left_mp + right_mp) // 2
    if midpoint == left_mp or midpoint == right_mp:
        raise MaterializedPathExhaustedError("Run 'lmk compact'")
    return midpoint
```

**Compaction**:
```python
def compact_siblings(siblings):
    count = len(siblings)
    tier = 100 if count <= 9 else (10 if count <= 99 else 1)
    return [i * tier for i in range(1, count + 1)]
```

---

## R4: YAML Frontmatter Parsing Best Practices

### Decision
Use **PyYAML 6.0.2+ with safe_load** for frontmatter parsing, with custom delimiter detection.

### Rationale
- **Security**: `safe_load` prevents arbitrary code execution (constitution § Security)
- **Standard format**: Three-dash delimiter (`---`) is markdown ecosystem standard (Jekyll, Hugo, Obsidian)
- **Simple structure**: Only need to parse `title:` field for MVP (FR-004)
- **Error tolerance**: Malformed YAML triggers warning, continues (per clarification on error handling)

### Alternatives Considered
- **python-frontmatter library**: Adds dependency for trivial parsing task (5-10 lines of code)
- **Regex extraction**: Fragile for multi-line titles or complex YAML
- **TOML frontmatter**: Non-standard in markdown ecosystem

### Implementation Notes
```python
import yaml
from pathlib import Path

def parse_frontmatter(content: str) -> dict:
    if not content.startswith('---\n'):
        return {}
    parts = content.split('---\n', 2)
    if len(parts) < 3:
        return {}
    try:
        return yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        logger.warning(f"Invalid YAML frontmatter: {e}")
        return {}
```

**Title extraction**: `frontmatter.get('title', '')` with fallback to slugified filename if missing.

---

## R5: Filename Parsing Regex Pattern

### Decision
Use **compiled regex with named groups** for filename parsing per FR-030 pattern.

### Rationale
- **Performance**: Compiled regex faster than repeated string splits for 1000+ files (SC-004)
- **Clarity**: Named groups make intent explicit and code self-documenting
- **Validation**: Single regex enforces all format rules (3-digit segments, valid SQID characters, .md extension)

### Alternatives Considered
- **String split operations**: More lines of code, slower, harder to validate format
- **Pathlib suffixes only**: Doesn't validate internal structure

### Implementation Notes
```python
import re

# Pattern: <mp>_<sqid>_<type>_<optional-slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)

def parse_filename(filename: str) -> dict | None:
    match = FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return {
        'mp': match.group('mp'),
        'sqid': match.group('sqid'),
        'type': match.group('type'),
        'slug': match.group('slug'),
        'depth': match.group('mp').count('-') + 1
    }
```

---

## R6: Python Slugify Configuration

### Decision
Use **python-slugify 8.0.0+** with default settings (ASCII transliteration).

### Rationale
- **URL-safe output**: Converts special characters to ASCII equivalents (FR-005, FR-038)
- **Predictable**: Same input always produces same slug (testable)
- **Handles unicode**: Converts "Writer's Guide: Advanced!" → "Writers-Guide-Advanced"
- **Battle-tested**: Used by Django, Flask, and other major frameworks

### Alternatives Considered
- **Manual regex replacement**: Fragile, doesn't handle unicode properly
- **unicodedata.normalize**: Lower-level, requires additional sanitization logic

### Implementation Notes
```python
from slugify import slugify

slug = slugify(title, lowercase=True, separator='-')
# "Chapter One" → "chapter-one"
# "Writer's Guide!" → "writers-guide"
```

---

## R7: Filesystem Atomicity Strategy

### Decision
Use **atomic rename with temporary file suffix** for move operations; **direct operations** for add/delete.

### Rationale
- **Move operations**: Use `Path.rename()` (atomic on POSIX, near-atomic on Windows) with temp suffix (`.tmp`) to avoid collisions during batch renames (FR-012).
- **Add operations**: Direct `Path.write_text()` - no collision risk for new files.
- **Delete operations**: Direct `Path.unlink()` - fail-fast if file locked (FR-042).
- **No rollback**: Per FR-042, fail fast with descriptive error. Git provides recovery.

### Alternatives Considered
- **Transaction log**: Over-engineered for MVP, adds complexity violation
- **Two-phase commit**: Unnecessary given git recovery and fail-fast policy

### Implementation Notes
```python
def atomic_batch_rename(renames: list[tuple[Path, Path]]):
    # Phase 1: Rename to .tmp
    for old, new in renames:
        old.rename(old.with_suffix('.md.tmp'))

    # Phase 2: Rename from .tmp to final
    for old, new in renames:
        old.with_suffix('.md.tmp').rename(new)
```

---

## R8: Tree Rendering Algorithm

### Decision
Use **depth-first traversal with Unicode box-drawing characters** for human-readable output (FR-021).

### Rationale
- **Standard CLI convention**: Matches `tree` command, `git log --graph`, etc.
- **Unicode characters**: `├──`, `│  `, `└──` for visual hierarchy
- **Compact**: Fits 100-node outline on single screen
- **Performance**: O(N) single-pass traversal meets SC-002 (<2s for 100 nodes)

### Alternatives Considered
- **Indentation only**: Less visual distinction between levels
- **ASCII-only**: Less readable, but could be fallback for `--ascii` flag (future)

### Implementation Notes
```python
def render_tree(nodes, prefix='', is_last=True):
    connector = '└── ' if is_last else '├── '
    print(f"{prefix}{connector}{node.title} (@{node.sqid})")

    extension = '    ' if is_last else '│   '
    for i, child in enumerate(node.children):
        render_tree(child, prefix + extension, i == len(node.children) - 1)
```

---

## Summary of Research Decisions

| Area | Technology/Approach | Key Rationale |
|------|---------------------|---------------|
| Identifiers | sqids-python 0.5.0+ | Short, deterministic, collision-resistant |
| CLI Framework | Click 8.1.8+ | Explicit control, battle-tested, constitution-compliant |
| Path Calculation | Tiered numbering + interval halving | Predictable, testable, user-transparent |
| YAML Parsing | PyYAML safe_load | Secure, standard, simple |
| Filename Parsing | Compiled regex with named groups | Fast, validated, self-documenting |
| Slugification | python-slugify 8.0.0+ | Unicode-aware, URL-safe, predictable |
| Filesystem Ops | Atomic rename + fail-fast | POSIX-compliant, aligns with FR-042 |
| Tree Rendering | DFS + Unicode box chars | Standard, compact, fast |

All research areas resolved. **No blockers for Phase 1 design**.
