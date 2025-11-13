"""Use case for deleting outline nodes."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.domain.entities import Node, Outline
    from linemark.ports.filesystem import FileSystemPort

# Pattern for parsing filenames: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)


class DeleteNodeUseCase:
    """Use case for deleting nodes with various strategies."""

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize use case with filesystem adapter.

        Args:
            filesystem: Filesystem port implementation

        """
        self.filesystem = filesystem

    def execute(
        self,
        sqid: str,
        directory: Path,
        recursive: bool = False,  # noqa: FBT001, FBT002
        promote: bool = False,  # noqa: FBT001, FBT002
    ) -> list[Node]:
        """Delete a node using the specified strategy.

        Args:
            sqid: SQID of node to delete
            directory: Working directory for outline
            recursive: If True, delete node and all descendants
            promote: If True, delete node but promote children to parent level

        Returns:
            List of deleted nodes

        Raises:
            ValueError: If node not found, has children without flags, or both flags set

        """
        # Validate flags
        if recursive and promote:
            msg = 'Cannot use both recursive and promote flags'
            raise ValueError(msg)

        # Build outline from filesystem
        outline = self._build_outline(directory)

        # Execute appropriate delete strategy
        if promote:
            deleted_nodes, promoted_nodes = outline.delete_node_promote(sqid)
            # Delete files for deleted node
            self._delete_node_files(deleted_nodes, directory)
            # Rename files for promoted nodes
            self._rename_promoted_files(promoted_nodes, directory)
            return deleted_nodes

        deleted_nodes = outline.delete_node_recursive(sqid) if recursive else outline.delete_node(sqid)

        # Delete files for all deleted nodes
        self._delete_node_files(deleted_nodes, directory)

        return deleted_nodes

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

    def _delete_node_files(self, nodes: list[Node], directory: Path) -> None:
        """Delete all files for given nodes.

        Args:
            nodes: Nodes whose files should be deleted
            directory: Working directory

        """
        for node in nodes:
            for doc_type in node.document_types:
                filename = node.filename(doc_type)
                filepath = directory / filename
                if self.filesystem.file_exists(filepath):  # pragma: no branch
                    self.filesystem.delete_file(filepath)

    def _rename_promoted_files(self, promoted_nodes: list[Node], directory: Path) -> None:
        """Rename files for promoted nodes.

        Args:
            promoted_nodes: Nodes that were promoted to new level
            directory: Working directory

        """
        # Renamed files need to match the new MP in the node
        all_files = self.filesystem.list_markdown_files(directory)

        for node in promoted_nodes:
            # Find current files for this node (with old MP)
            node_files = [f for f in all_files if f'_{node.sqid.value}_' in f.name]

            for old_filepath in node_files:
                match = FILENAME_PATTERN.match(old_filepath.name)
                if not match:
                    continue  # pragma: no cover

                # Generate new filename with updated MP
                doc_type = match.group('type')
                new_filename = node.filename(doc_type)
                new_filepath = directory / new_filename

                # Only rename if MP changed
                if old_filepath != new_filepath:  # pragma: no branch
                    content = self.filesystem.read_file(old_filepath)
                    self.filesystem.write_file(new_filepath, content)
                    self.filesystem.delete_file(old_filepath)
