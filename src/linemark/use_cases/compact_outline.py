"""Use case for compacting outline node spacing."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.domain.entities import MaterializedPath, Node, Outline
    from linemark.ports.filesystem import FileSystemPort

# Pattern for parsing filenames: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)


class CompactOutlineUseCase:
    """Use case for compacting node spacing using tiered redistribution."""

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize use case with filesystem adapter.

        Args:
            filesystem: Filesystem port implementation

        """
        self.filesystem = filesystem

    def execute(self, sqid: str | None, directory: Path) -> list[Node]:
        """Compact sibling spacing at specified level.

        Args:
            sqid: Parent SQID to compact children of (None = compact root level)
            directory: Working directory for outline

        Returns:
            List of nodes that were renumbered

        Raises:
            ValueError: If sqid provided but not found

        """
        # Build outline from filesystem
        outline = self._build_outline(directory)

        # Identify siblings to compact
        if sqid is None:
            # Compact root-level nodes
            siblings = outline.root_nodes()
            parent_mp = None
        else:
            # Compact children of specified node
            parent_node = outline.get_by_sqid(sqid)
            if parent_node is None:
                msg = f'Node with SQID {sqid} not found'
                raise ValueError(msg)

            # Find immediate children
            siblings = [
                n
                for n in outline.nodes.values()
                if len(n.mp.segments) == len(parent_node.mp.segments) + 1
                and n.mp.segments[: len(parent_node.mp.segments)] == parent_node.mp.segments
            ]
            parent_mp = parent_node.mp

        if not siblings:
            return []  # pragma: no cover

        # Sort siblings by current MP
        siblings.sort(key=lambda n: n.mp.segments[-1])

        # Calculate new MPs using tiered redistribution
        count = len(siblings)
        tier = 100 if count <= 9 else (10 if count <= 99 else 1)  # noqa: PLR2004

        # Create rename map: sqid -> (node, new_mp)
        rename_map: list[tuple[Node, tuple[int, ...]]] = []
        for i, sibling in enumerate(siblings, start=1):
            new_position = i * tier
            new_mp_segments = (new_position,) if parent_mp is None else (*parent_mp.segments, new_position)

            rename_map.append((sibling, new_mp_segments))

        # Apply renames (update MPs in outline and rename files)
        renamed_nodes = []
        for node, new_mp_segments in rename_map:
            old_mp = node.mp

            # Update node MP
            from linemark.domain.entities import MaterializedPath

            new_mp = MaterializedPath(segments=new_mp_segments)
            node.mp = new_mp
            renamed_nodes.append(node)

            # Update all descendants
            descendants = [
                n
                for n in outline.nodes.values()
                if len(n.mp.segments) > len(old_mp.segments)
                and n.mp.segments[: len(old_mp.segments)] == old_mp.segments
            ]

            for desc in descendants:
                desc.mp = desc.mp.replace_prefix(old_mp, new_mp)

            # Rename files on filesystem
            self._rename_node_files(node, old_mp, directory)

            # Rename descendant files
            for desc in descendants:
                old_desc_mp = MaterializedPath(
                    segments=(
                        *old_mp.segments,
                        *desc.mp.segments[len(new_mp.segments) :],
                    )
                )
                self._rename_node_files(desc, old_desc_mp, directory)

        return renamed_nodes

    def _build_outline(self, directory: Path) -> Outline:  # noqa: PLR0914
        """Build Outline from filesystem.

        Args:
            directory: Working directory

        Returns:
            Outline with all nodes loaded from files

        """
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        all_files = self.filesystem.list_markdown_files(directory)
        nodes: dict[str, Node] = {}

        # Track SQIDs we've seen to avoid duplicates
        seen_sqids: set[str] = set()

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if not match:
                continue  # pragma: no cover

            sqid_str = match.group('sqid')

            # Skip if we've already processed this SQID
            if sqid_str in seen_sqids:
                continue

            seen_sqids.add(sqid_str)

            # Parse node details from draft file
            mp_str = match.group('mp')
            slug = match.group('slug')

            # Read title from draft file
            draft_path = directory / f'{mp_str}_{sqid_str}_draft_{slug}.md'
            if self.filesystem.file_exists(draft_path):
                content = self.filesystem.read_file(draft_path)
                parts = content.split('---')
                if len(parts) >= 3:  # noqa: PLR2004
                    frontmatter = yaml.safe_load(parts[1])
                    title = frontmatter.get('title', 'Untitled')
                else:
                    title = 'Untitled'  # pragma: no cover
            else:  # pragma: no cover
                title = 'Untitled'  # pragma: no cover

            # Find all document types for this node
            node_files = [f for f in all_files if f'_{sqid_str}_' in f.name]
            doc_types = set()
            for nf in node_files:
                nf_match = FILENAME_PATTERN.match(nf.name)
                if nf_match:  # pragma: no branch
                    doc_types.add(nf_match.group('type'))

            # Create node
            node = Node(
                sqid=SQID(value=sqid_str),
                mp=MaterializedPath.from_string(mp_str),
                title=title,
                slug=slug or '',
                document_types=doc_types,
            )

            nodes[sqid_str] = node

        return Outline(nodes=nodes)

    def _rename_node_files(self, node: Node, old_mp: MaterializedPath, directory: Path) -> None:
        """Rename all files for a node from old MP to new MP.

        Args:
            node: Node with updated MP
            old_mp: Previous materialized path
            directory: Working directory

        """
        # Generate old and new filenames
        for doc_type in node.document_types:
            old_filename = f'{old_mp.as_string}_{node.sqid.value}_{doc_type}_{node.slug}.md'
            new_filename = node.filename(doc_type)

            old_path = directory / old_filename
            new_path = directory / new_filename

            # Only rename if file exists and names differ
            if self.filesystem.file_exists(old_path) and old_filename != new_filename:
                content = self.filesystem.read_file(old_path)
                self.filesystem.write_file(new_path, content)
                self.filesystem.delete_file(old_path)
