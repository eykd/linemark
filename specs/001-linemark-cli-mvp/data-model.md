# Data Model: Linemark

**Feature**: Linemark - Hierarchical Markdown Outline Manager
**Date**: 2025-11-12
**Phase**: 1 (Design)

## Overview

This document defines the domain entities, value objects, and their relationships for Linemark. All entities are implemented as Pydantic models for validation and type safety (constitution § Required Stack).

---

## Value Objects

### MaterializedPath

**Purpose**: Encodes hierarchical position and sibling order using lexicographically sortable path segments.

**Structure**:
```python
from pydantic import BaseModel, Field, field_validator

class MaterializedPath(BaseModel):
    """Materialized path value object."""

    segments: tuple[int, ...] = Field(
        ...,
        description="Path segments as integers (001, 100, 050, etc.)",
        min_length=1
    )

    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        """Ensure all segments are 1-999."""
        if any(seg < 1 or seg > 999 for seg in v):
            raise ValueError("All segments must be between 001 and 999")
        return v

    @property
    def depth(self) -> int:
        """Depth in hierarchy (1 for root, 2 for child, etc.)."""
        return len(self.segments)

    @property
    def as_string(self) -> str:
        """String representation: '001-100-050'."""
        return '-'.join(f"{seg:03d}" for seg in self.segments)

    @classmethod
    def from_string(cls, path_str: str) -> 'MaterializedPath':
        """Parse from string like '001-100-050'."""
        segments = tuple(int(seg) for seg in path_str.split('-'))
        return cls(segments=segments)

    def parent(self) -> 'MaterializedPath | None':
        """Get parent path (None if root)."""
        if self.depth == 1:
            return None
        return MaterializedPath(segments=self.segments[:-1])

    def child(self, position: int) -> 'MaterializedPath':
        """Create child path at given position."""
        return MaterializedPath(segments=self.segments + (position,))
```

**Validation Rules**:
- **FR-002**: Three-digit segments (001-999)
- **FR-029**: Validate format and dash separators
- **FR-037**: Support depth ≥5 (tuple supports arbitrary depth)

**State Transitions**: Immutable value object (no transitions)

---

### SQID

**Purpose**: Stable, unique identifier for nodes that persists across renames and moves.

**Structure**:
```python
from pydantic import BaseModel, Field, field_validator

class SQID(BaseModel):
    """SQID value object (URL-safe short identifier)."""

    value: str = Field(
        ...,
        description="Base-62 encoded identifier (e.g., 'A3F7c')",
        min_length=1,
        max_length=20
    )

    @field_validator('value')
    @classmethod
    def validate_sqid(cls, v: str) -> str:
        """Ensure alphanumeric only."""
        if not v.isalnum():
            raise ValueError("SQID must be alphanumeric")
        return v

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SQID):
            return False
        return self.value == other.value
```

**Validation Rules**:
- **FR-001**: Unique, stable across operations
- **FR-006**: Identifiable by @ prefix in CLI (not stored in value object)
- **FR-032**: Generated from monotonic counter

**State Transitions**: Immutable value object (no transitions)

---

### DocumentType

**Purpose**: Categorize different content files associated with a node.

**Structure**:
```python
from enum import Enum

class DocumentType(str, Enum):
    """Document type enumeration."""

    DRAFT = "draft"
    NOTES = "notes"
    CUSTOM = "custom"  # For user-defined types

    @classmethod
    def from_string(cls, type_str: str) -> 'DocumentType':
        """Parse from lowercase string."""
        try:
            return cls(type_str.lower())
        except ValueError:
            return cls.CUSTOM

    def is_required(self) -> bool:
        """Check if this type is required for all nodes."""
        return self in (DocumentType.DRAFT, DocumentType.NOTES)
```

**Validation Rules**:
- **FR-003**: draft and notes are required
- **FR-018**: Support arbitrary types
- **FR-020**: Listable per node

**State Transitions**: None (enum)

---

## Entities

### Node

**Purpose**: Logical entry in outline hierarchy, aggregating all document files for a position.

**Structure**:
```python
from pydantic import BaseModel, Field
from pathlib import Path

class Node(BaseModel):
    """Outline node entity."""

    sqid: SQID = Field(..., description="Stable unique identifier")
    mp: MaterializedPath = Field(..., description="Hierarchical position")
    title: str = Field(..., min_length=1, description="Canonical title from draft frontmatter")
    slug: str = Field(..., min_length=1, description="URL-friendly slug from title")
    document_types: set[str] = Field(
        default_factory=lambda: {"draft", "notes"},
        description="Document types present for this node"
    )

    def filename(self, doc_type: str) -> str:
        """Generate filename for given document type."""
        # Format: <mp>_<sqid>_<type>_<slug>.md
        return f"{self.mp.as_string}_{self.sqid.value}_{doc_type}_{self.slug}.md"

    def filenames(self) -> list[str]:
        """Get all filenames for this node."""
        return [self.filename(dt) for dt in sorted(self.document_types)]

    def has_children(self, all_nodes: list['Node']) -> bool:
        """Check if this node has children in the outline."""
        return any(
            n.mp.parent() == self.mp
            for n in all_nodes
            if n.sqid != self.sqid
        )

    def get_children(self, all_nodes: list['Node']) -> list['Node']:
        """Get direct children of this node."""
        return sorted(
            [n for n in all_nodes if n.mp.parent() == self.mp],
            key=lambda n: n.mp.as_string
        )

    def validate_required_types(self) -> bool:
        """Ensure draft and notes types exist."""
        return "draft" in self.document_types and "notes" in self.document_types
```

**Validation Rules**:
- **FR-001**: SQID uniqueness enforced at Outline level
- **FR-004**: Title from draft frontmatter
- **FR-005**: Slug generated from title
- **FR-028**: Required types (draft, notes) validated

**State Transitions**:
- **Created** → Node with MP, SQID, title, draft + notes files
- **Moved** → MP changes, SQID preserved
- **Renamed** → Title and slug change, SQID and MP preserved
- **Type Added** → document_types expanded
- **Type Removed** → document_types reduced (except required types)
- **Deleted** → Node removed, children optionally promoted or deleted

---

## Aggregate Root

### Outline

**Purpose**: Manages the complete hierarchical structure and enforces invariants.

**Structure**:
```python
from pydantic import BaseModel, Field

class Outline(BaseModel):
    """Outline aggregate root."""

    nodes: dict[str, Node] = Field(
        default_factory=dict,
        description="Nodes indexed by SQID value"
    )
    next_counter: int = Field(
        default=1,
        description="Next SQID counter value"
    )

    def get_by_sqid(self, sqid: SQID | str) -> Node | None:
        """Retrieve node by SQID."""
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        return self.nodes.get(sqid_str)

    def get_by_mp(self, mp: MaterializedPath | str) -> Node | None:
        """Retrieve node by materialized path."""
        mp_obj = MaterializedPath.from_string(mp) if isinstance(mp, str) else mp
        return next(
            (n for n in self.nodes.values() if n.mp == mp_obj),
            None
        )

    def all_sorted(self) -> list[Node]:
        """Get all nodes sorted by materialized path."""
        return sorted(self.nodes.values(), key=lambda n: n.mp.as_string)

    def root_nodes(self) -> list[Node]:
        """Get root-level nodes (depth 1)."""
        return [n for n in self.nodes.values() if n.mp.depth == 1]

    def validate_invariants(self) -> list[str]:
        """Check outline integrity, return list of violations."""
        violations = []

        # Check SQID uniqueness
        sqids = [n.sqid.value for n in self.nodes.values()]
        if len(sqids) != len(set(sqids)):
            violations.append("Duplicate SQIDs detected")

        # Check materialized path uniqueness
        mps = [n.mp.as_string for n in self.nodes.values()]
        if len(mps) != len(set(mps)):
            violations.append("Duplicate materialized paths detected")

        # Check required document types
        for node in self.nodes.values():
            if not node.validate_required_types():
                violations.append(f"Node {node.sqid.value} missing required types")

        return violations

    def find_next_sibling_position(self, parent_mp: MaterializedPath | None) -> int:
        """Find next available sibling position under parent."""
        siblings = [
            n for n in self.nodes.values()
            if n.mp.parent() == parent_mp
        ]
        if not siblings:
            return 100  # First child at tier 100

        max_position = max(n.mp.segments[-1] for n in siblings)
        if max_position >= 999:
            raise ValueError("No space for new sibling (run 'lmk compact')")

        # Use tier spacing: 100 for first, then 10s, then 1s
        tier = 100 if len(siblings) < 9 else (10 if len(siblings) < 99 else 1)
        return max_position + tier
```

**Invariants Enforced**:
- **FR-001**: SQID uniqueness across outline
- **FR-002**: Valid materialized path format
- **FR-028**: Required document types (draft, notes) present
- **FR-031**: Lexicographic sorting by MP

**State Transitions**:
- **Initialized** → Empty or loaded from filesystem scan
- **Node Added** → nodes dict updated, next_counter incremented
- **Node Moved** → Affected nodes' MPs updated
- **Node Deleted** → Node removed from dict (+ descendants or promote children)
- **Compacted** → MPs renumbered with ideal spacing

---

## Relationships

```
Outline (1) ──< contains >── (N) Node
Node (1) ──< has >── (1) MaterializedPath
Node (1) ──< identified by >── (1) SQID
Node (1) ──< includes >── (N) DocumentType
Node (1) ──< parent of >── (N) Node [self-referential via MP hierarchy]
```

**Hierarchy Encoding**:
- Parent-child: `Node.mp.parent() == Parent.mp`
- Siblings: Share same `mp.parent()`, sorted by `mp.segments[-1]`
- Depth: `Node.mp.depth`

---

## Filesystem Representation

Each `Node` materializes as N files where N = `len(document_types)`:

**Example**:
```
Node(
  sqid="A3F7c",
  mp="001-100",
  title="Chapter One",
  slug="chapter-one",
  document_types={"draft", "notes", "characters"}
)
```

**Files**:
```
001-100_A3F7c_draft_chapter-one.md      # Contains YAML frontmatter with title
001-100_A3F7c_notes_chapter-one.md      # Empty or user content
001-100_A3F7c_characters_chapter-one.md # User content
```

**Parsing**: Use `FILENAME_PATTERN` regex (see research.md R5) to extract MP, SQID, type, slug.

---

## Validation Summary

| Entity | Validation Rule | FR Reference |
|--------|----------------|--------------|
| MaterializedPath | Segments 001-999, depth ≥1 | FR-002, FR-029, FR-037 |
| SQID | Alphanumeric, unique | FR-001, FR-032 |
| Node | Required types, unique SQID+MP | FR-003, FR-028 |
| Outline | No duplicate SQIDs/MPs | FR-001, FR-002 |

All validations enforced at domain layer using Pydantic validators and Outline invariant checks.
