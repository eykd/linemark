"""Port protocol for writing document type content.

This module defines the contract for writing document type files
to the filesystem with atomic guarantees. Implementations must preserve
YAML frontmatter and use atomic write operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class WriteTypePort(Protocol):
    """Protocol for writing document type content to files atomically.

    Implementations must:
    - Preserve existing YAML frontmatter when updating files
    - Use atomic write operations (temp file + rename)
    - Create minimal frontmatter for new files
    - Handle both empty and non-empty stdin content
    """

    def write_type_body(
        self,
        sqid: str,
        doctype: str,
        body: str,
        directory: Path,
    ) -> None:
        """Write body content to a document type file atomically.

        If the file exists, preserves existing YAML frontmatter and replaces
        only the body content. If the file doesn't exist, creates it with
        minimal frontmatter (sqid, doctype).

        Uses atomic write operations (write to temp file, then rename) to
        ensure the original file remains intact if the operation fails.

        Args:
            sqid: Node identifier (without @ prefix)
            doctype: Document type name (e.g., 'notes', 'characters')
            body: New body content to write (can be empty string)
            directory: Directory containing the outline files

        Raises:
            NodeNotFoundError: If no file exists for the SQID
            FileNotFoundError: If directory doesn't exist
            PermissionError: If file/directory is not writable
            OSError: If disk is full or other filesystem errors

        """
        ...

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
            Absolute path where the document type file exists or should be created

        Raises:
            NodeNotFoundError: If no file exists for the SQID

        """
        ...

    def read_frontmatter(
        self,
        path: Path,
    ) -> dict[str, object]:
        """Read YAML frontmatter from an existing file.

        Args:
            path: Absolute path to the file

        Returns:
            Frontmatter as dictionary (empty dict if no frontmatter)

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            ValueError: If YAML frontmatter is invalid

        """
        ...

    def write_file_atomic(
        self,
        path: Path,
        content: str,
    ) -> None:
        """Write content to file atomically.

        Uses temp file + rename pattern to ensure atomicity. If the write
        fails or is interrupted, the original file (if it exists) remains
        intact.

        Args:
            path: Absolute path to the target file
            content: Full file content (frontmatter + body)

        Raises:
            PermissionError: If file/directory is not writable
            OSError: If disk is full or other filesystem errors

        """
        ...
