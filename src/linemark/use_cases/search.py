"""Use case for searching across document types.

This use case orchestrates the SearchPort to search for patterns
across the outline with optional filtering.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from linemark.ports.search import SearchPort, SearchResult


class SearchUseCase:
    """Use case for searching across document types.

    Orchestrates SearchPort to search for patterns across outline files,
    with support for filtering by subtree and doctype, and formatting
    results as plaintext or JSON.
    """

    def __init__(self, search_port: SearchPort) -> None:
        """Initialize use case with port.

        Args:
            search_port: Port for search operations

        """
        self.search_port = search_port

    def execute(
        self,
        pattern: str,
        directory: Path,
        *,
        subtree_sqid: str | None = None,
        doctypes: list[str] | None = None,
        case_sensitive: bool = False,
        multiline: bool = False,
        literal: bool = False,
    ) -> Iterator[SearchResult]:
        """Execute search operation.

        Args:
            pattern: Search pattern (regex or literal string)
            directory: Directory containing the outline files
            subtree_sqid: Optional SQID to filter by subtree (e.g., '100-200')
            doctypes: Optional list of document types to filter by
            case_sensitive: If True, match case exactly
            multiline: If True, allow . to match newlines (re.DOTALL)
            literal: If True, treat pattern as literal string

        Yields:
            SearchResult objects for each match

        Raises:
            InvalidRegexError: If pattern is invalid regex
            FileNotFoundError: If directory doesn't exist
            PermissionError: If files are not readable
            UnicodeDecodeError: If files are not valid UTF-8

        """
        # Compile pattern
        compiled_pattern = self.search_port.compile_pattern(
            pattern,
            case_sensitive=case_sensitive,
            multiline=multiline,
            literal=literal,
        )

        # Search outline
        yield from self.search_port.search_outline(
            compiled_pattern,
            directory,
            subtree_sqid=subtree_sqid,
            doctypes=doctypes,
        )
