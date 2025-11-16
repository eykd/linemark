"""Use case for reading document type content.

This use case orchestrates the ReadTypePort to read and return
document type body content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.read_type import ReadTypePort


class ReadTypeUseCase:
    """Use case for reading document type content.

    Orchestrates ReadTypePort to read body content from document type files.
    """

    def __init__(self, read_type_port: ReadTypePort) -> None:
        """Initialize use case with port.

        Args:
            read_type_port: Port for reading document types

        """
        self.read_type_port = read_type_port

    def execute(
        self,
        sqid: str,
        doctype: str,
        directory: Path,
    ) -> str:
        """Execute read operation.

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
        return self.read_type_port.read_type_body(sqid, doctype, directory)
