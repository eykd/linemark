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

    def replace_prefix(
        self,
        old_prefix: MaterializedPath,
        new_prefix: MaterializedPath,
    ) -> MaterializedPath:
        """Replace prefix in this path for move operations.

        Args:
            old_prefix: Prefix to replace (e.g., '100')
            new_prefix: New prefix (e.g., '200')

        Returns:
            New path with prefix replaced

        Raises:
            ValueError: If this path doesn't start with old_prefix

        """
        # Check if path starts with old_prefix
        if len(self.segments) < len(old_prefix.segments):
            msg = f'Path {self.as_string} does not start with prefix {old_prefix.as_string}'
            raise ValueError(msg)

        if self.segments[: len(old_prefix.segments)] != old_prefix.segments:
            msg = f'Path {self.as_string} does not start with prefix {old_prefix.as_string}'
            raise ValueError(msg)

        # Replace prefix: new_prefix + remaining segments
        remaining_segments = self.segments[len(old_prefix.segments) :]
        return MaterializedPath(segments=(*new_prefix.segments, *remaining_segments))


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

    def validate_invariants(self) -> list[str]:
        """Check outline integrity, return list of violations.

        Returns:
            List of violation messages (empty if valid)

        """
        violations = []

        # Check SQID uniqueness
        sqids = [n.sqid.value for n in self.nodes.values()]
        if len(sqids) != len(set(sqids)):
            violations.append('Duplicate SQIDs detected')

        # Check materialized path uniqueness
        mps = [n.mp.as_string for n in self.nodes.values()]
        if len(mps) != len(set(mps)):
            violations.append('Duplicate materialized paths detected')

        # Check required document types
        violations.extend(
            f'Node {node.sqid.value} missing required types'
            for node in self.nodes.values()
            if not node.validate_required_types()
        )

        return violations

    def find_next_sibling_position(self, parent_mp: MaterializedPath | None) -> int:
        """Find next available sibling position under parent.

        Uses tiered numbering: 100 for first tier, 10 for mid, 1 for fine.

        Args:
            parent_mp: Parent materialized path (None for root level)

        Returns:
            Next available position integer (001-999)

        Raises:
            ValueError: If no space available (999 siblings exist)

        """
        siblings = [n for n in self.nodes.values() if n.mp.parent() == parent_mp]

        if not siblings:
            return 100  # First child at tier 100

        max_position = max(n.mp.segments[-1] for n in siblings)
        if max_position >= MAX_SEGMENT_VALUE:
            msg = "No space for new sibling (run 'lmk compact')"
            raise ValueError(msg)

        # Use tier spacing based on sibling count (per data-model.md):
        # Tier 100: for first 9 siblings (100, 200, 300, ..., 900)
        # Tier 10: for next 90 siblings (010-900 in 10s)
        # Tier 1: for remaining siblings (1-unit increments)
        tier = 100 if len(siblings) < 9 else (10 if len(siblings) < 99 else 1)  # noqa: PLR2004
        return max_position + tier

    def add_node(self, node: Node) -> None:
        """Add a new node to the outline.

        Args:
            node: Node to add

        Raises:
            ValueError: If SQID or materialized path already exists

        """
        # Check for duplicate SQID
        if node.sqid.value in self.nodes:
            msg = f'SQID {node.sqid.value} already exists in outline'
            raise ValueError(msg)

        # Check for duplicate materialized path
        if any(n.mp == node.mp for n in self.nodes.values()):
            msg = f'Materialized path {node.mp.as_string} already exists in outline'
            raise ValueError(msg)

        # Add node to outline
        self.nodes[node.sqid.value] = node

        # Increment counter
        self.next_counter += 1

    def move_node(self, sqid: SQID | str, new_mp: MaterializedPath) -> None:
        """Move node to new position, cascading to all descendants.

        Args:
            sqid: SQID of node to move
            new_mp: New materialized path for the node

        Raises:
            ValueError: If node not found or target position occupied

        """
        # Find node to move
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        node = self.get_by_sqid(sqid_str)
        if node is None:
            msg = f'Node with SQID {sqid_str} not found'
            raise ValueError(msg)

        # Check if target position is available (unless moving to own position)
        if new_mp != node.mp and any(n.mp == new_mp for n in self.nodes.values()):
            msg = f'Target path {new_mp.as_string} already occupied'
            raise ValueError(msg)

        # Find all descendants (nodes with MP starting with this node's MP)
        old_mp = node.mp
        descendants = [
            n
            for n in self.nodes.values()
            if len(n.mp.segments) > len(old_mp.segments) and n.mp.segments[: len(old_mp.segments)] == old_mp.segments
        ]

        # Update node's materialized path
        node.mp = new_mp

        # Cascade update to descendants
        for desc in descendants:
            desc.mp = desc.mp.replace_prefix(old_mp, new_mp)

    def delete_node(self, sqid: SQID | str) -> list[Node]:
        """Delete a leaf node (node with no children).

        Args:
            sqid: SQID of node to delete

        Returns:
            List containing the deleted node

        Raises:
            ValueError: If node not found or node has children

        """
        # Find node to delete
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        node = self.get_by_sqid(sqid_str)
        if node is None:
            msg = f'Node with SQID {sqid_str} not found'
            raise ValueError(msg)

        # Check if node has children
        children = [
            n
            for n in self.nodes.values()
            if len(n.mp.segments) == len(node.mp.segments) + 1
            and n.mp.segments[: len(node.mp.segments)] == node.mp.segments
        ]

        if children:
            msg = 'Cannot delete node with children. Use delete_node_recursive or delete_node_promote instead.'
            raise ValueError(msg)

        # Delete the node
        del self.nodes[sqid_str]
        return [node]

    def delete_node_recursive(self, sqid: SQID | str) -> list[Node]:
        """Delete node and all its descendants recursively.

        Args:
            sqid: SQID of node to delete

        Returns:
            List of all deleted nodes (node + descendants)

        Raises:
            ValueError: If node not found

        """
        # Find node to delete
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        node = self.get_by_sqid(sqid_str)
        if node is None:
            msg = f'Node with SQID {sqid_str} not found'
            raise ValueError(msg)

        # Find all descendants (nodes with MP starting with this node's MP)
        descendants = [
            n
            for n in self.nodes.values()
            if len(n.mp.segments) > len(node.mp.segments) and n.mp.segments[: len(node.mp.segments)] == node.mp.segments
        ]

        # Collect all nodes to delete
        to_delete = [node, *descendants]

        # Delete all nodes
        for n in to_delete:
            del self.nodes[n.sqid.value]

        return to_delete

    def delete_node_promote(self, sqid: SQID | str) -> tuple[list[Node], list[Node]]:
        """Delete node and promote its children to parent level.

        Children are moved one level up and renumbered at their new level.
        Grandchildren (and deeper descendants) are updated accordingly.

        Args:
            sqid: SQID of node to delete

        Returns:
            Tuple of (deleted_nodes, promoted_nodes)
            - deleted_nodes: List containing only the deleted node
            - promoted_nodes: List of immediate children that were promoted

        Raises:
            ValueError: If node not found

        """
        # Find node to delete
        sqid_str = sqid.value if isinstance(sqid, SQID) else sqid
        node = self.get_by_sqid(sqid_str)
        if node is None:
            msg = f'Node with SQID {sqid_str} not found'
            raise ValueError(msg)

        # Find immediate children (direct children only)
        children = [
            n
            for n in self.nodes.values()
            if len(n.mp.segments) == len(node.mp.segments) + 1
            and n.mp.segments[: len(node.mp.segments)] == node.mp.segments
        ]

        # If node is at root, children stay at root but need new positions
        # If node has parent, children move to parent level
        new_parent_mp = None if node.mp.depth == 1 else node.mp.parent()

        # Promote each child
        promoted_nodes: list[Node] = []
        for child in children:
            # Get all descendants of this child
            child_descendants = [
                n
                for n in self.nodes.values()
                if len(n.mp.segments) > len(child.mp.segments)
                and n.mp.segments[: len(child.mp.segments)] == child.mp.segments
            ]

            # Calculate new position for child at parent level
            if new_parent_mp is None:
                # Promote to root - find next available position
                position_int = self.find_next_sibling_position(None)
                new_position = MaterializedPath(segments=(position_int,))
            else:
                # Promote to parent level - find next available sibling position
                position_int = self.find_next_sibling_position(new_parent_mp)
                new_position = MaterializedPath(segments=(*new_parent_mp.segments, position_int))

            # Store old MP for descendants update
            old_child_mp = child.mp

            # Update child MP
            child.mp = new_position
            promoted_nodes.append(child)

            # Update all descendants of this child
            for desc in child_descendants:
                desc.mp = desc.mp.replace_prefix(old_child_mp, new_position)

        # Delete the node
        del self.nodes[sqid_str]

        return ([node], promoted_nodes)
