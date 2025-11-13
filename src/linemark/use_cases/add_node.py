"""Add node use case."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort
    from linemark.ports.slugifier import SlugifierPort
    from linemark.ports.sqid_generator import SQIDGeneratorPort

# Filename pattern per FR-030: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$',
)


class AddNodeUseCase:
    """Use case for adding a new node to the outline.

    Orchestrates domain logic with filesystem, SQID generation, and slugification
    to create a new outline node with draft and notes files.
    """

    def __init__(
        self,
        filesystem: FileSystemPort,
        sqid_generator: SQIDGeneratorPort,
        slugifier: SlugifierPort,
    ) -> None:
        """Initialize the use case.

        Args:
            filesystem: Filesystem port for reading/writing files
            sqid_generator: SQID generator port for creating identifiers
            slugifier: Slugifier port for creating URL-friendly slugs

        """
        self.filesystem = filesystem
        self.sqid_generator = sqid_generator
        self.slugifier = slugifier
        self.outline: Outline | None = None

    def _load_outline(self, directory: Path) -> Outline:
        """Load existing outline from directory or create new one.

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
                continue

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
                    continue

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

        # Derive next counter from existing SQIDs
        if outline.nodes:
            counters = [self.sqid_generator.decode(sqid) for sqid in outline.nodes]
            valid_counters = [c for c in counters if c is not None]
            if valid_counters:  # pragma: no branch
                outline.next_counter = max(valid_counters) + 1

        return outline

    def _extract_title_from_frontmatter(self, content: str) -> str:  # noqa: PLR6301
        """Extract title from YAML frontmatter.

        Args:
            content: File content with YAML frontmatter

        Returns:
            Title string from frontmatter, or 'Untitled' if not found

        """
        if not content.startswith('---\n'):
            return 'Untitled'

        parts = content.split('---\n', 2)
        if len(parts) < 3:  # noqa: PLR2004
            return 'Untitled'

        frontmatter = parts[1]
        for line in frontmatter.split('\n'):
            if line.startswith('title:'):
                return line.split('title:', 1)[1].strip()

        return 'Untitled'

    def execute(
        self,
        title: str,
        directory: Path,
        parent_sqid: str | None = None,
        sibling_sqid: str | None = None,
        before: bool = False,  # noqa: ARG002, FBT001, FBT002
    ) -> Node:
        """Execute the add node use case.

        Args:
            title: Node title
            directory: Working directory for outline
            parent_sqid: Optional parent node SQID for creating child
            sibling_sqid: Optional sibling node SQID for positioning
            before: If True with sibling_sqid, insert before sibling

        Returns:
            Created Node object

        Raises:
            ValueError: If parent or sibling SQID not found

        """
        # Load or create outline
        if self.outline is None:
            self.outline = self._load_outline(directory)

        # Determine materialized path for new node
        if parent_sqid is not None:
            parent_node = self.outline.get_by_sqid(parent_sqid)
            if parent_node is None:
                msg = f'Parent node with SQID {parent_sqid} not found'
                raise ValueError(msg)

            parent_mp = parent_node.mp
            next_position = self.outline.find_next_sibling_position(parent_mp)
            mp = parent_mp.child(next_position)

        elif sibling_sqid is not None:
            sibling_node = self.outline.get_by_sqid(sibling_sqid)
            if sibling_node is None:
                msg = f'Sibling node with SQID {sibling_sqid} not found'
                raise ValueError(msg)

            sibling_parent_mp = sibling_node.mp.parent()
            next_position = self.outline.find_next_sibling_position(sibling_parent_mp)
            if sibling_parent_mp is None:
                mp = MaterializedPath(segments=(next_position,))
            else:
                mp = sibling_parent_mp.child(next_position)

        else:
            # Root level node
            next_position = self.outline.find_next_sibling_position(None)
            mp = MaterializedPath(segments=(next_position,))

        # Generate SQID
        sqid_str = self.sqid_generator.encode(self.outline.next_counter)
        sqid = SQID(value=sqid_str)

        # Generate slug
        slug = self.slugifier.slugify(title)

        # Create node
        node = Node(
            sqid=sqid,
            mp=mp,
            title=title,
            slug=slug,
            document_types={'draft', 'notes'},
        )

        # Add to outline
        self.outline.add_node(node)

        # Write files
        draft_filename = node.filename('draft')
        draft_content = f"""---
title: {title}
---

"""
        self.filesystem.write_file(directory / draft_filename, draft_content)

        notes_filename = node.filename('notes')
        self.filesystem.write_file(directory / notes_filename, '')

        return node
