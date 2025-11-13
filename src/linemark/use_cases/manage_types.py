"""Use case for managing document types for outline nodes."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort

# Pattern for parsing filenames: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)

# Required types that cannot be removed
REQUIRED_TYPES = {'draft', 'notes'}


class ManageTypesUseCase:
    """Use case for managing document types associated with nodes."""

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize use case with filesystem adapter.

        Args:
            filesystem: Filesystem port implementation

        """
        self.filesystem = filesystem

    def list_types(self, sqid: str, directory: Path) -> list[str]:
        """List all document types for a node.

        Args:
            sqid: SQID of node to query
            directory: Working directory for outline

        Returns:
            Sorted list of document type names

        """
        # Scan directory for files matching SQID
        all_files = self.filesystem.list_markdown_files(directory)
        types: set[str] = set()

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if match and match.group('sqid') == sqid:  # pragma: no branch
                types.add(match.group('type'))

        return sorted(types)

    def add_type(self, sqid: str, doc_type: str, directory: Path) -> None:
        """Add new document type to a node.

        Creates a new empty file with the specified document type.
        Validates that the node exists and the type doesn't already exist.

        Args:
            sqid: SQID of node to modify
            doc_type: Document type to add (e.g., 'characters')
            directory: Working directory for outline

        Raises:
            ValueError: If node not found or type already exists

        """
        # Load existing types and find node metadata
        all_files = self.filesystem.list_markdown_files(directory)
        node_files = []
        existing_types: set[str] = set()

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if match and match.group('sqid') == sqid:  # pragma: no branch
                node_files.append(filepath)
                existing_types.add(match.group('type'))

        # Validate node exists
        if not node_files:
            msg = f'Node with SQID {sqid} not found'
            raise ValueError(msg)

        # Validate type doesn't already exist
        if doc_type in existing_types:
            msg = f'Type {doc_type} already exists for node {sqid}'
            raise ValueError(msg)

        # Extract MP and slug from existing file (use draft file)
        draft_file = next((f for f in node_files if '_draft_' in f.name), node_files[0])
        match = FILENAME_PATTERN.match(draft_file.name)
        if not match:  # pragma: no cover
            msg = f'Invalid filename format: {draft_file.name}'
            raise ValueError(msg)

        mp = match.group('mp')
        slug = match.group('slug') or ''

        # Create new file
        new_filename = f'{mp}_{sqid}_{doc_type}_{slug}.md'
        new_filepath = directory / new_filename
        self.filesystem.write_file(new_filepath, '')

    def remove_type(self, sqid: str, doc_type: str, directory: Path) -> None:
        """Remove document type from a node.

        Deletes the file for the specified document type.
        Cannot remove required types (draft, notes).

        Args:
            sqid: SQID of node to modify
            doc_type: Document type to remove
            directory: Working directory for outline

        Raises:
            ValueError: If node not found, type not found, or attempting to remove required type

        """
        # Validate not removing required type
        if doc_type in REQUIRED_TYPES:
            msg = f'Cannot remove required type: {doc_type}'
            raise ValueError(msg)

        # Find all files for node
        all_files = self.filesystem.list_markdown_files(directory)
        node_files = []
        target_file = None

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if match and match.group('sqid') == sqid:  # pragma: no branch
                node_files.append(filepath)
                if match.group('type') == doc_type:
                    target_file = filepath

        # Validate node exists
        if not node_files:
            msg = f'Node with SQID {sqid} not found'
            raise ValueError(msg)

        # Validate type exists
        if target_file is None:
            msg = f'Type {doc_type} not found for node {sqid}'
            raise ValueError(msg)

        # Delete file
        self.filesystem.delete_file(target_file)
