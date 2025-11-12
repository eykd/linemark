"""Domain entities and value objects for Linemark."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# Materialized path segment constraints
MIN_SEGMENT_VALUE = 1
MAX_SEGMENT_VALUE = 999


class MaterializedPath(BaseModel):
    """Materialized path value object.

    Encodes hierarchical position and sibling order using lexicographically
    sortable path segments (001-999).
    """

    segments: tuple[int, ...] = Field(
        ...,
        description='Path segments as integers (001, 100, 050, etc.)',
        min_length=1,
    )

    @field_validator('segments')
    @classmethod
    def validate_segments(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        """Ensure all segments are within valid range."""
        if any(seg < MIN_SEGMENT_VALUE or seg > MAX_SEGMENT_VALUE for seg in v):
            msg = f'All segments must be between {MIN_SEGMENT_VALUE:03d} and {MAX_SEGMENT_VALUE:03d}'
            raise ValueError(msg)
        return v

    @property
    def depth(self) -> int:
        """Depth in hierarchy (1 for root, 2 for child, etc.)."""
        return len(self.segments)

    @property
    def as_string(self) -> str:
        """String representation: '001-100-050'."""
        return '-'.join(f'{seg:03d}' for seg in self.segments)

    @classmethod
    def from_string(cls, path_str: str) -> MaterializedPath:
        """Parse from string like '001-100-050'.

        Args:
            path_str: Dash-separated path segments (e.g., '001-100-050')

        Returns:
            MaterializedPath instance

        Raises:
            ValueError: If path_str is empty, non-numeric, or segments out of range

        """
        if not path_str:
            msg = 'Path string cannot be empty'
            raise ValueError(msg)

        try:
            segments = tuple(int(seg) for seg in path_str.split('-'))
        except ValueError as e:
            msg = f'Invalid path format: {path_str!r}'
            raise ValueError(msg) from e

        return cls(segments=segments)

    def parent(self) -> MaterializedPath | None:
        """Get parent path (None if root)."""
        if self.depth == 1:
            return None
        return MaterializedPath(segments=self.segments[:-1])

    def child(self, position: int) -> MaterializedPath:
        """Create child path at given position."""
        return MaterializedPath(segments=(*self.segments, position))


class SQID(BaseModel):
    """SQID value object (URL-safe short identifier).

    Stable, unique identifier for nodes that persists across renames and moves.
    """

    value: str = Field(
        ...,
        description="Base-62 encoded identifier (e.g., 'A3F7c')",
        min_length=1,
        max_length=20,
    )

    @field_validator('value')
    @classmethod
    def validate_sqid(cls, v: str) -> str:
        """Ensure alphanumeric only."""
        if not v.isalnum():
            msg = 'SQID must be alphanumeric'
            raise ValueError(msg)
        return v

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __hash__(self) -> int:
        """Hash for use in sets and dicts."""
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if not isinstance(other, SQID):
            return False
        return self.value == other.value


class Node(BaseModel):
    """Outline node entity.

    Logical entry in outline hierarchy, aggregating all document files
    for a position.
    """

    sqid: SQID = Field(..., description='Stable unique identifier')
    mp: MaterializedPath = Field(..., description='Hierarchical position')
    title: str = Field(..., min_length=1, description='Canonical title from draft frontmatter')
    slug: str = Field(..., min_length=1, description='URL-friendly slug from title')
    document_types: set[str] = Field(
        default_factory=lambda: {'draft', 'notes'},
        description='Document types present for this node',
    )

    def filename(self, doc_type: str) -> str:
        """Generate filename for given document type.

        Args:
            doc_type: Document type (e.g., 'draft', 'notes', 'characters')

        Returns:
            Filename in format: <mp>_<sqid>_<type>_<slug>.md

        """
        return f'{self.mp.as_string}_{self.sqid.value}_{doc_type}_{self.slug}.md'

    def filenames(self) -> list[str]:
        """Get all filenames for this node.

        Returns:
            List of filenames sorted alphabetically by document type

        """
        return [self.filename(dt) for dt in sorted(self.document_types)]

    def validate_required_types(self) -> bool:
        """Ensure draft and notes types exist.

        Returns:
            True if both draft and notes are present, False otherwise

        """
        return 'draft' in self.document_types and 'notes' in self.document_types


class Outline(BaseModel):
    """Outline aggregate root.

    Manages the complete hierarchical structure and enforces invariants.
    """

    nodes: dict[str, Node] = Field(
        default_factory=dict,
        description='Nodes indexed by SQID value',
    )
    next_counter: int = Field(
        default=1,
        description='Next SQID counter value',
    )

    def get_by_sqid(self, sqid: SQID | str) -> Node | None:
        """Retrieve node by SQID.

        Args:
            sqid: SQID object or string value

        Returns:
            Node if found, None otherwise

        """
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        return self.nodes.get(sqid_str)

    def get_by_mp(self, mp: MaterializedPath | str) -> Node | None:
        """Retrieve node by materialized path.

        Args:
            mp: MaterializedPath object or string representation

        Returns:
            Node if found, None otherwise

        """
        mp_obj = MaterializedPath.from_string(mp) if isinstance(mp, str) else mp
        return next(
            (n for n in self.nodes.values() if n.mp == mp_obj),
            None,
        )

    def all_sorted(self) -> list[Node]:
        """Get all nodes sorted by materialized path.

        Returns:
            List of nodes sorted lexicographically by materialized path

        """
        return sorted(self.nodes.values(), key=lambda n: n.mp.as_string)

    def root_nodes(self) -> list[Node]:
        """Get root-level nodes (depth 1).

        Returns:
            List of nodes at the root level

        """
        return [n for n in self.nodes.values() if n.mp.depth == 1]
