"""Adapter for reading document type content from filesystem.

This adapter implements ReadTypePort and handles YAML frontmatter parsing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import anyio
import yaml

from linemark.domain.exceptions import DoctypeNotFoundError, NodeNotFoundError

if TYPE_CHECKING:
    from pathlib import Path


class ReadTypeAdapter:
    """Adapter for reading document type content from filesystem.

    Implements ReadTypePort protocol by locating files based on SQID and doctype,
    parsing YAML frontmatter, and returning body content.
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
        file_path = await self.resolve_file_path(sqid, doctype, directory)

        # Read file content using anyio
        content = await anyio.Path(file_path).read_text(encoding='utf-8')

        # Parse frontmatter and body
        _, body = self._split_frontmatter_and_body(content)

        return body

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
        # Find all files matching the SQID pattern using anyio
        from pathlib import Path as PathlibPath

        directory_anyio = anyio.Path(directory)
        pattern = f'*_{sqid}_*.md'
        matching_files = [PathlibPath(p) async for p in directory_anyio.glob(pattern)]

        if not matching_files:
            msg = f'Node @{sqid} not found'
            raise NodeNotFoundError(msg)

        # Filter for the specific doctype
        doctype_pattern = f'*_{sqid}_{doctype}_*.md'
        doctype_files = [PathlibPath(p) async for p in directory_anyio.glob(doctype_pattern)]

        if not doctype_files:
            raise DoctypeNotFoundError(doctype, sqid)

        # Return first match (should only be one)
        return doctype_files[0].absolute()

    def _split_frontmatter_and_body(self, content: str) -> tuple[dict[str, object], str]:
        """Split file content into frontmatter and body.

        Args:
            content: Full file content

        Returns:
            Tuple of (frontmatter dict, body string)

        Raises:
            ValueError: If frontmatter format is invalid

        """
        if not content.startswith('---\n'):
            # No frontmatter, entire content is body
            return {}, content

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

        body = parts[2]

        return frontmatter, body
