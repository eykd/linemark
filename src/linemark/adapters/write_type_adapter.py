"""Adapter for writing document type content to filesystem.

This adapter implements WriteTypePort and handles atomic writes with
YAML frontmatter preservation.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path

import yaml

from linemark.domain.exceptions import DoctypeNotFoundError, NodeNotFoundError


class WriteTypeAdapter:
    """Adapter for writing document type content to filesystem.

    Implements WriteTypePort protocol by locating files based on SQID and doctype,
    preserving YAML frontmatter, and performing atomic write operations.
    """

    def write_type_body(
        self,
        sqid: str,
        doctype: str,
        body: str,
        directory: Path,
    ) -> None:
        """Write body content to a document type file atomically.

        Args:
            sqid: Node identifier (without @ prefix)
            doctype: Document type name (e.g., 'notes', 'characters')
            body: Body content to write (will be appended after frontmatter)
            directory: Directory containing the outline files

        Raises:
            NodeNotFoundError: If no file exists for the SQID
            DoctypeNotFoundError: If the specific doctype file doesn't exist
            FileNotFoundError: If directory doesn't exist
            PermissionError: If file is not writable

        """
        file_path = self.resolve_file_path(sqid, doctype, directory)

        # Read existing frontmatter
        frontmatter = self.read_frontmatter(file_path)

        # Construct new content
        new_content = self._construct_file_content(frontmatter, body)

        # Atomic write
        self.write_file_atomic(file_path, new_content)

    def resolve_file_path(
        self,
        sqid: str,
        doctype: str,
        directory: Path,
    ) -> Path:
        """Resolve the filesystem path for a document type file.

        Args:
            sqid: Node identifier (without @ prefix)
            doctype: Document type name
            directory: Directory containing the outline files

        Returns:
            Absolute path to the document type file

        Raises:
            NodeNotFoundError: If no file exists for the SQID
            DoctypeNotFoundError: If the specific doctype file doesn't exist

        """
        # Find all files matching the SQID pattern
        pattern = f'*_{sqid}_*.md'
        matching_files = list(directory.glob(pattern))

        if not matching_files:
            msg = f'Node @{sqid} not found'
            raise NodeNotFoundError(msg)

        # Filter for the specific doctype
        doctype_pattern = f'*_{sqid}_{doctype}_*.md'
        doctype_files = list(directory.glob(doctype_pattern))

        if not doctype_files:
            raise DoctypeNotFoundError(doctype, sqid)

        # Return first match (should only be one)
        return doctype_files[0].absolute()

    def read_frontmatter(self, file_path: Path) -> dict[str, object]:
        """Read YAML frontmatter from an existing file.

        Args:
            file_path: Path to the file to read

        Returns:
            Dictionary of frontmatter metadata (empty dict if no frontmatter)

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            UnicodeDecodeError: If file is not valid UTF-8
            ValueError: If frontmatter is malformed

        """
        content = file_path.read_text(encoding='utf-8')

        if not content.startswith('---\n'):
            # No frontmatter
            return {}

        # Split by --- delimiter
        parts = content.split('---\n', 2)
        if len(parts) < 3:  # pragma: no cover
            raise ValueError('Invalid frontmatter format: missing closing ---')

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(parts[1]) or {}
        except yaml.YAMLError as e:  # pragma: no cover
            msg = f'Invalid YAML frontmatter: {e}'
            raise ValueError(msg) from e

        return frontmatter

    def write_file_atomic(self, file_path: Path, content: str) -> None:
        """Write content to file atomically using temp file + rename.

        Args:
            file_path: Path to the file to write
            content: Content to write

        Raises:
            PermissionError: If file or directory is not writable
            OSError: If atomic rename fails

        """
        # Create temp file in same directory to ensure same filesystem
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix='.tmp_',
            suffix='.md',
            text=True,
        )

        try:
            # Write content to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)

            # Atomic rename (os.replace handles cross-platform atomicity)
            Path(temp_path).replace(file_path)
        except Exception:  # pragma: no cover
            # Clean up temp file on error
            with contextlib.suppress(OSError):
                Path(temp_path).unlink()
            raise

    def _construct_file_content(
        self,
        frontmatter: dict[str, object],
        body: str,
    ) -> str:
        """Construct file content from frontmatter and body.

        Args:
            frontmatter: YAML frontmatter dictionary
            body: Body content

        Returns:
            Complete file content with frontmatter and body

        """
        if not frontmatter:
            # No frontmatter, just return body
            return body

        # Serialize frontmatter to YAML
        yaml_content = yaml.safe_dump(
            frontmatter,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

        # Construct complete content
        return f'---\n{yaml_content}---\n{body}'
