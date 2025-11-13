"""Move node use case."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort

# Filename pattern per FR-030: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$',
)


class MoveNodeUseCase:
    """Use case for moving a node to a new position in the outline.

    Orchestrates domain logic with filesystem to move node and all descendants,
    updating materialized paths and renaming files atomically.
    """

    def __init__(
        self,
        filesystem: FileSystemPort,
    ) -> None:
        """Initialize the use case.

        Args:
            filesystem: Filesystem port for reading/writing/renaming files

        """
        self.filesystem = filesystem

    def _load_outline(self, directory: Path) -> Outline:
        """Load existing outline from directory.

        Args:
            directory: Directory containing markdown files

        Returns:
            Outline object with existing nodes loaded

        """
        outline = Outline()

        # List all markdown files
        md_files = self.filesystem.list_markdown_files(directory)

        # Parse each file
        for file_path in md_files:
            match = FILENAME_PATTERN.match(file_path.name)
            if not match:
                continue  # pragma: no cover

            mp_str = match.group('mp')
            sqid_str = match.group('sqid')
            doc_type = match.group('type')
            slug = match.group('slug') or ''

            # Get or create node for this SQID
            node = outline.get_by_sqid(sqid_str)
            if node is None:
                # Read title from draft file
                if doc_type == 'draft':
                    content = self.filesystem.read_file(file_path)
                    title = self._extract_title_from_frontmatter(content)
                else:
                    # Skip non-draft files if node doesn't exist yet
                    continue  # pragma: no cover

                # Create new node
                node = Node(
                    sqid=SQID(value=sqid_str),
                    mp=MaterializedPath.from_string(mp_str),
                    title=title,
                    slug=slug,
                    document_types=set(),
                )
                outline.nodes[sqid_str] = node

            # Add document type
            node.document_types.add(doc_type)

        return outline

    def _extract_title_from_frontmatter(self, content: str) -> str:  # noqa: PLR6301
        """Extract title from YAML frontmatter.

        Args:
            content: File content with YAML frontmatter

        Returns:
            Title string from frontmatter, or 'Untitled' if not found

        """
        if not content.startswith('---\n'):
            return 'Untitled'  # pragma: no cover

        parts = content.split('---\n', 2)
        if len(parts) < 3:  # noqa: PLR2004
            return 'Untitled'  # pragma: no cover

        frontmatter = parts[1]
        for line in frontmatter.split('\n'):
            if line.startswith('title:'):  # pragma: no branch
                return line.split('title:', 1)[1].strip()

        return 'Untitled'  # pragma: no cover

    def execute(
        self,
        sqid: str,
        new_mp_str: str,
        directory: Path,
    ) -> None:
        """Execute the move node use case.

        Args:
            sqid: SQID of node to move
            new_mp_str: New materialized path as string (e.g., '200-100')
            directory: Working directory for outline

        Raises:
            ValueError: If node not found or target position occupied

        """
        # Load outline
        outline = self._load_outline(directory)

        # Parse new MP
        new_mp = MaterializedPath.from_string(new_mp_str)

        # Get node to move
        node = outline.get_by_sqid(sqid)
        if node is None:
            msg = f'Node with SQID {sqid} not found'
            raise ValueError(msg)

        # Save old MP for file renaming
        old_mp = node.mp

        # Move node in domain (this validates and cascades to descendants)
        outline.move_node(sqid, new_mp)

        # Collect all nodes that were affected (node + descendants)
        affected_nodes = [
            n for n in outline.nodes.values() if n.sqid.value == sqid or self._is_descendant_of(n, new_mp)
        ]

        # Rename files for all affected nodes
        for affected_node in affected_nodes:
            # Determine what the old MP was for this node
            if affected_node.sqid.value == sqid:
                node_old_mp = old_mp
            else:
                # For descendants, reverse the prefix replacement to get old MP
                node_old_mp = affected_node.mp.replace_prefix(new_mp, old_mp)

            # Rename all document type files
            for doc_type in affected_node.document_types:
                old_filename = f'{node_old_mp.as_string}_{affected_node.sqid.value}_{doc_type}_{affected_node.slug}.md'
                new_filename = affected_node.filename(doc_type)

                old_path = directory / old_filename
                new_path = directory / new_filename

                # Rename file
                self.filesystem.rename_file(old_path, new_path)

    def _is_descendant_of(self, node: Node, ancestor_mp: MaterializedPath) -> bool:  # noqa: PLR6301
        """Check if node is a descendant of the given materialized path.

        Args:
            node: Node to check
            ancestor_mp: Potential ancestor materialized path

        Returns:
            True if node is a descendant, False otherwise

        """
        # Node is descendant if its MP starts with ancestor_mp and is longer
        return (
            len(node.mp.segments) > len(ancestor_mp.segments)
            and node.mp.segments[: len(ancestor_mp.segments)] == ancestor_mp.segments
        )
