"""Use case for writing document type content.

This use case orchestrates the WriteTypePort to write body content
to document type files.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.write_type import WriteTypePort


class WriteTypeUseCase:
    """Use case for writing document type content.

    Orchestrates WriteTypePort to write body content to document type files
    with atomic guarantees and frontmatter preservation.
    """

    def __init__(self, write_type_port: WriteTypePort) -> None:
        """Initialize use case with port.

        Args:
            write_type_port: Port for writing document types

        """
        self.write_type_port = write_type_port

    def execute(
        self,
        sqid: str,
        doctype: str,
        body: str,
        directory: Path,
    ) -> None:
        """Execute write operation.

        Args:
            sqid: Node identifier (without @ prefix)
            doctype: Document type name (e.g., 'notes', 'characters')
            body: Body content to write
            directory: Directory containing the outline files

        Raises:
            NodeNotFoundError: If no file exists for the SQID
            DoctypeNotFoundError: If the specific doctype file doesn't exist
            FileNotFoundError: If directory doesn't exist
            PermissionError: If file is not writable
            ValueError: If file format is invalid (malformed frontmatter)

        """
        self.write_type_port.write_type_body(sqid, doctype, body, directory)
