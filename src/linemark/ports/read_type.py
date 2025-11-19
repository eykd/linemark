"""Port protocol for reading document type content.

This module defines the contract for reading document type files
from the filesystem. Implementations must handle YAML frontmatter
parsing and return only the body content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class ReadTypePort(Protocol):
    """Protocol for reading document type content from files.

    Implementations must:
    - Locate the correct file based on SQID, doctype, and directory
    - Parse YAML frontmatter to extract metadata
    - Return only the body content (everything after second --- delimiter)
    - Raise appropriate exceptions for missing files or invalid formats
    """

    async def read_type_body(
        self,
        sqid: str,
        doctype: str,
        directory: Path,
    ) -> str:
        """Read the body content of a document type file.

        Args:
            sqid: Node identifier (without @ prefix)
            doctype: Document type name (e.g., 'notes', 'characters')
            directory: Directory containing the outline files

        Returns:
            Body content as string (excluding YAML frontmatter)

        Raises:
            NodeNotFoundError: If no file exists for the SQID
            DoctypeNotFoundError: If the specific doctype file doesn't exist
            FileNotFoundError: If directory doesn't exist
            PermissionError: If file is not readable
            UnicodeDecodeError: If file is not valid UTF-8
            ValueError: If file format is invalid (malformed frontmatter)

        """
        ...

    async def resolve_file_path(
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
        ...
