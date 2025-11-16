"""Port protocol for searching document content.

This module defines the contract for searching across document type files
using regex patterns. Implementations must handle pattern compilation,
line-by-line matching, and result ordering.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator


class SearchResult(BaseModel):
    """Represents a single search match.

    Attributes:
        sqid: Node identifier (without @ prefix)
        filename: Full filename of the document type file
        line_number: Line number where match was found (1-indexed)
        content: The matching line content (without trailing newline)
        path: Full path to the file (for internal use, not displayed)

    """

    sqid: str
    filename: str
    line_number: int
    content: str
    path: Path

    model_config = ConfigDict(arbitrary_types_allowed=True)  # Allow Path type


class SearchPort(Protocol):
    """Protocol for searching document content across the outline.

    Implementations must:
    - Compile regex patterns with appropriate flags
    - Search files in outline position order
    - Support filtering by subtree and doctype
    - Return results with line numbers and content
    - Handle both plaintext and JSON output formats
    """

    def compile_pattern(
        self,
        pattern: str,
        *,
        case_sensitive: bool = False,
        multiline: bool = False,
        literal: bool = False,
    ) -> re.Pattern[str]:
        """Compile a search pattern with appropriate flags.

        Args:
            pattern: Search pattern (regex or literal string)
            case_sensitive: If True, match case exactly
            multiline: If True, allow . to match newlines (re.DOTALL)
            literal: If True, treat pattern as literal string (escape regex)

        Returns:
            Compiled regex pattern

        Raises:
            InvalidRegexError: If pattern is invalid regex

        """
        ...

    def search_file(
        self,
        path: Path,
        pattern: re.Pattern[str],
    ) -> Iterator[tuple[int, str]]:
        """Search a single file for pattern matches.

        Searches line-by-line for memory efficiency. Yields matches as
        (line_number, content) tuples.

        Args:
            path: Absolute path to the file to search
            pattern: Compiled regex pattern

        Yields:
            Tuples of (line_number, content) for each match

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            UnicodeDecodeError: If file is not valid UTF-8

        """
        ...

    def get_files_in_outline_order(
        self,
        directory: Path,
        *,
        subtree_sqid: str | None = None,
        doctypes: list[str] | None = None,
    ) -> Iterator[Path]:
        """Get files to search in outline position order.

        Files are returned in hierarchical order (depth-first traversal)
        based on filename sorting. Optionally filter by subtree and/or
        document types.

        Args:
            directory: Directory containing the outline files
            subtree_sqid: If provided, only include files in this subtree
            doctypes: If provided, only include files of these types

        Yields:
            Absolute paths to files in outline order

        Raises:
            FileNotFoundError: If directory doesn't exist
            NodeNotFoundError: If subtree_sqid doesn't exist

        """
        ...

    def extract_sqid_from_filename(
        self,
        filename: str,
    ) -> str:
        """Extract SQID from a linemark filename.

        Parses the filename pattern NNN-NNN-NNN_SQID_DOCTYPE_SLUG.md
        to extract just the SQID component.

        Args:
            filename: Filename to parse

        Returns:
            SQID (without @ prefix)

        Raises:
            ValueError: If filename doesn't match expected pattern

        """
        ...

    def search_outline(
        self,
        pattern: re.Pattern[str],
        directory: Path,
        *,
        subtree_sqid: str | None = None,
        doctypes: list[str] | None = None,
    ) -> Iterator[SearchResult]:
        """Search across the outline for pattern matches.

        Combines get_files_in_outline_order and search_file to search
        the entire outline (or filtered subset) and yield SearchResult
        objects in outline order.

        Args:
            pattern: Compiled regex pattern
            directory: Directory containing the outline files
            subtree_sqid: If provided, only search this subtree
            doctypes: If provided, only search these document types

        Yields:
            SearchResult objects for each match, in outline order

        Raises:
            FileNotFoundError: If directory doesn't exist
            NodeNotFoundError: If subtree_sqid doesn't exist

        """
        ...
