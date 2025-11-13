"""Use case for renaming outline nodes."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort
    from linemark.ports.slugifier import SlugifierPort

# Pattern for parsing filenames: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)

# Minimum number of parts expected from splitting on '---' for valid YAML frontmatter
FRONTMATTER_MIN_PARTS = 3


class RenameNodeUseCase:
    """Use case for renaming nodes and updating filenames."""

    def __init__(self, filesystem: FileSystemPort, slugifier: SlugifierPort) -> None:
        """Initialize use case with adapters.

        Args:
            filesystem: Filesystem port implementation
            slugifier: Slugifier port implementation

        """
        self.filesystem = filesystem
        self.slugifier = slugifier

    def _find_node_files(self, sqid: str, directory: Path) -> list[Path]:
        """Find all files belonging to a node.

        Args:
            sqid: SQID of node to find
            directory: Working directory for outline

        Returns:
            List of file paths for the node

        Raises:
            ValueError: If node not found

        """
        all_files = self.filesystem.list_markdown_files(directory)
        node_files: list[Path] = []

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if match and match.group('sqid') == sqid:
                node_files.append(filepath)

        if not node_files:
            msg = f'Node with SQID {sqid} not found'
            raise ValueError(msg)

        return node_files

    def _update_draft_file(
        self, draft_file: Path, mp: str, sqid: str, new_title: str, new_slug: str, old_slug: str
    ) -> None:
        """Update draft file with new title and rename if needed.

        Args:
            draft_file: Path to draft file
            mp: Materialized path
            sqid: SQID
            new_title: New title for frontmatter
            new_slug: New slug for filename
            old_slug: Old slug for comparison

        """
        # Read and parse draft file
        draft_content = self.filesystem.read_file(draft_file)

        # Split frontmatter and body
        parts = draft_content.split('---')
        if len(parts) >= FRONTMATTER_MIN_PARTS:  # pragma: no branch
            # Parse frontmatter
            frontmatter = yaml.safe_load(parts[1])
            frontmatter['title'] = new_title

            # Reconstruct content with updated frontmatter
            new_content = f'---\n{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---{parts[2]}'

            # Write updated draft to new filename
            new_draft_filename = f'{mp}_{sqid}_draft_{new_slug}.md'
            new_draft_path = draft_file.parent / new_draft_filename
            self.filesystem.write_file(new_draft_path, new_content)

            # Delete old draft file if slug changed
            if old_slug != new_slug:
                self.filesystem.delete_file(draft_file)

    def _rename_other_file(self, filepath: Path, mp: str, sqid: str, new_slug: str, old_slug: str) -> None:
        """Rename a non-draft file if slug changed.

        Args:
            filepath: Path to file to rename
            mp: Materialized path
            sqid: SQID
            new_slug: New slug for filename
            old_slug: Old slug for comparison

        """
        # Skip if slug hasn't changed
        if old_slug == new_slug:
            return

        # Read content
        content = self.filesystem.read_file(filepath)

        # Extract document type from filename
        match = FILENAME_PATTERN.match(filepath.name)
        if not match:
            return  # pragma: no cover

        doc_type = match.group('type')

        # Create new filename
        new_filename = f'{mp}_{sqid}_{doc_type}_{new_slug}.md'
        new_path = filepath.parent / new_filename

        # Write to new location and delete old
        self.filesystem.write_file(new_path, content)
        self.filesystem.delete_file(filepath)

    def execute(self, sqid: str, new_title: str, directory: Path) -> None:
        """Rename a node by updating title and filenames.

        Updates the title in the draft file's YAML frontmatter and renames
        all associated files to use the new slug.

        Args:
            sqid: SQID of node to rename
            new_title: New title for the node
            directory: Working directory for outline

        Raises:
            ValueError: If node not found

        """
        # Find all files for this node
        node_files = self._find_node_files(sqid, directory)

        # Generate new slug from new title
        new_slug = self.slugifier.slugify(new_title)

        # Extract MP from first file
        first_file = node_files[0]
        match = FILENAME_PATTERN.match(first_file.name)
        if not match:
            msg = f'Invalid filename format: {first_file.name}'  # pragma: no cover
            raise ValueError(msg)  # pragma: no cover

        mp = match.group('mp')
        old_slug = match.group('slug')

        # Find and update draft file
        draft_file = next((f for f in node_files if '_draft_' in f.name), None)
        if draft_file:  # pragma: no branch
            self._update_draft_file(draft_file, mp, sqid, new_title, new_slug, old_slug)

        # Rename all other files
        for filepath in node_files:
            if filepath == draft_file:
                continue  # Already handled draft file

            match = FILENAME_PATTERN.match(filepath.name)
            if not match:
                continue  # pragma: no cover

            file_old_slug = match.group('slug')
            self._rename_other_file(filepath, mp, sqid, new_slug, file_old_slug)
