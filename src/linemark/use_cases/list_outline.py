"""List outline use case."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from linemark.domain.entities import SQID, MaterializedPath, Node

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


class ListOutlineUseCase:
    """Use case for listing all nodes in the outline.

    Loads outline from filesystem and returns nodes sorted by materialized path.
    """

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize the use case.

        Args:
            filesystem: Filesystem port for reading files

        """
        self.filesystem = filesystem

    def _extract_title_from_frontmatter(self, content: str) -> str:  # noqa: PLR6301
        """Extract title from YAML frontmatter.

        Args:
            content: File content with YAML frontmatter

        Returns:
            Title string from frontmatter, or 'Untitled' if not found

        """
        if not content.startswith('---\n'):  # pragma: no cover
            return 'Untitled'

        parts = content.split('---\n', 2)
        if len(parts) < 3:  # noqa: PLR2004  # pragma: no cover
            return 'Untitled'

        frontmatter = parts[1]
        for line in frontmatter.split('\n'):
            if line.startswith('title:'):  # pragma: no branch
                return line.split('title:', 1)[1].strip()

        return 'Untitled'  # pragma: no cover

    def execute(self, directory: Path, root_sqid: str | None = None) -> list[Node]:
        """Execute the list outline use case.

        Args:
            directory: Working directory containing outline files
            root_sqid: Optional SQID to filter to subtree

        Returns:
            List of nodes (all or filtered subtree)

        Raises:
            ValueError: If root_sqid is invalid or not found

        """
        nodes_by_sqid: dict[str, Node] = {}

        # List all markdown files
        md_files = self.filesystem.list_markdown_files(directory)

        # Parse each file
        for file_path in md_files:
            match = FILENAME_PATTERN.match(file_path.name)
            if not match:
                continue

            mp_str = match.group('mp')
            sqid_str = match.group('sqid')
            doc_type = match.group('type')
            slug = match.group('slug') or ''

            # Get or create node for this SQID
            if sqid_str not in nodes_by_sqid:
                # Read title from draft file
                if doc_type == 'draft':
                    content = self.filesystem.read_file(file_path)
                    title = self._extract_title_from_frontmatter(content)
                else:  # pragma: no cover
                    # Skip non-draft files if node doesn't exist yet
                    continue

                # Create new node
                node = Node(
                    sqid=SQID(value=sqid_str),
                    mp=MaterializedPath.from_string(mp_str),
                    title=title,
                    slug=slug,
                    document_types=set(),
                )
                nodes_by_sqid[sqid_str] = node

            # Add document type
            nodes_by_sqid[sqid_str].document_types.add(doc_type)

        # Get all nodes sorted by materialized path
        all_nodes = sorted(nodes_by_sqid.values(), key=lambda n: n.mp.as_string)

        # Filter to subtree if requested
        if root_sqid:
            return self._filter_to_subtree(all_nodes, root_sqid)

        return all_nodes

    def _filter_to_subtree(self, all_nodes: list[Node], root_sqid: str) -> list[Node]:
        """Filter nodes to subtree rooted at the given SQID.

        Args:
            all_nodes: All nodes in the outline
            root_sqid: SQID of the subtree root

        Returns:
            List containing root node and its descendants

        Raises:
            ValueError: If root_sqid not found in nodes

        """
        # Find root node
        root_node = next((n for n in all_nodes if n.sqid.value == root_sqid), None)
        if root_node is None:
            msg = f'SQID {root_sqid} not found in outline'
            raise ValueError(msg)

        # Check if orphaned
        if self._is_orphaned(root_node, all_nodes):
            # Return only the orphaned node
            return [root_node]

        # Get subtree
        return self._get_subtree(root_node, all_nodes)

    def _is_orphaned(self, node: Node, all_nodes: list[Node]) -> bool:  # noqa: PLR6301
        """Check if node is orphaned (parent doesn't exist).

        Args:
            node: Node to check
            all_nodes: All nodes in the outline

        Returns:
            True if node is orphaned, False otherwise

        """
        # Root nodes (depth 1) cannot be orphaned
        if node.mp.depth == 1:
            return False

        # Check if parent exists
        parent_mp = node.mp.parent()
        return not any(n.mp == parent_mp for n in all_nodes)

    def _get_subtree(self, root_node: Node, all_nodes: list[Node]) -> list[Node]:  # noqa: PLR6301
        """Get subtree rooted at the given node.

        Args:
            root_node: Root of the subtree
            all_nodes: All nodes in the outline

        Returns:
            List containing root node and all its descendants

        """
        # Get root MP segments
        root_segments = root_node.mp.segments

        # Find all descendants (nodes whose MP starts with root's MP)
        subtree = [root_node]
        for node in all_nodes:
            if node == root_node:
                continue
            # Check if node is a descendant
            node_segments = node.mp.segments
            if len(node_segments) > len(root_segments) and node_segments[: len(root_segments)] == root_segments:
                subtree.append(node)

        return subtree
