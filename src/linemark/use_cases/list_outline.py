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

    def execute(self, directory: Path) -> list[Node]:
        """Execute the list outline use case.

        Args:
            directory: Working directory containing outline files

        Returns:
            List of nodes sorted by materialized path

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

        # Return nodes sorted by materialized path
        return sorted(nodes_by_sqid.values(), key=lambda n: n.mp.as_string)
