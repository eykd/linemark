"""Adapter for searching across document type files.

This adapter implements SearchPort and handles regex matching,
file iteration in outline order, and result generation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from linemark.domain.search import compile_search_pattern, extract_sqid_from_filename
from linemark.ports.search import SearchResult

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator
    from pathlib import Path


class SearchAdapter:
    """Adapter for searching across document type files.

    Implements SearchPort protocol by compiling regex patterns, iterating
    through files in outline order, and generating search results.
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
        return compile_search_pattern(
            pattern,
            case_sensitive=case_sensitive,
            multiline=multiline,
            literal=literal,
        )

    def search_file(
        self,
        path: Path,
        pattern: re.Pattern[str],
    ) -> Iterator[tuple[int, str]]:
        """Search a single file for pattern matches.

        Args:
            path: Path to file to search
            pattern: Compiled regex pattern

        Yields:
            Tuples of (line_number, line_content) for matching lines

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If file is not readable
            UnicodeDecodeError: If file is not valid UTF-8

        """
        content = path.read_text(encoding='utf-8')
        lines = content.splitlines()

        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line):
                yield line_number, line

    def get_files_in_outline_order(
        self,
        directory: Path,
        *,
        subtree_sqid: str | None = None,
        doctypes: list[str] | None = None,
    ) -> Iterator[Path]:
        """Get files in outline order with optional filtering.

        Args:
            directory: Directory containing outline files
            subtree_sqid: Optional SQID to filter by subtree (e.g., '100-200')
            doctypes: Optional list of document types to filter by

        Yields:
            Paths to files in outline order (sorted by filename)

        Raises:
            FileNotFoundError: If directory doesn't exist

        """
        # Build glob pattern
        if subtree_sqid and doctypes:
            # Filter by both subtree and doctypes
            for doctype in doctypes:
                pattern = f'{subtree_sqid}*_{doctype}_*.md'
                yield from sorted(directory.glob(pattern))
        elif subtree_sqid:
            # Filter by subtree only
            pattern = f'{subtree_sqid}*.md'
            yield from sorted(directory.glob(pattern))
        elif doctypes:
            # Filter by doctypes only
            for doctype in doctypes:
                pattern = f'*_{doctype}_*.md'
                yield from sorted(directory.glob(pattern))
        else:
            # No filters, search only linemark outline files (pattern: *_*_*.md)
            # This matches files with at least 2 underscores (position_SQID_doctype_slug.md)
            # and excludes non-linemark files like README.md
            yield from sorted(directory.glob('*_*_*.md'))

    def extract_sqid_from_filename(self, filename: str) -> str:
        """Extract SQID from a linemark filename.

        Args:
            filename: Filename to parse

        Returns:
            SQID (without @ prefix)

        Raises:
            ValueError: If filename doesn't match expected pattern

        """
        return extract_sqid_from_filename(filename)

    def search_outline(
        self,
        pattern: re.Pattern[str],
        directory: Path,
        *,
        subtree_sqid: str | None = None,
        doctypes: list[str] | None = None,
    ) -> Iterator[SearchResult]:
        """Search across outline files for pattern matches.

        Args:
            pattern: Compiled regex pattern
            directory: Directory containing outline files
            subtree_sqid: Optional SQID to filter by subtree
            doctypes: Optional list of document types to filter by

        Yields:
            SearchResult objects for each match

        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If files are not readable
            UnicodeDecodeError: If files are not valid UTF-8

        """
        files = self.get_files_in_outline_order(
            directory,
            subtree_sqid=subtree_sqid,
            doctypes=doctypes,
        )

        for file_path in files:
            filename = file_path.name

            # Extract SQID from filename
            try:
                sqid = self.extract_sqid_from_filename(filename)
            except ValueError:  # pragma: no cover
                # Skip files that don't match expected pattern
                continue

            # Search file for matches
            for line_number, content in self.search_file(file_path, pattern):
                yield SearchResult(
                    sqid=sqid,
                    filename=filename,
                    line_number=line_number,
                    content=content,
                    path=file_path,
                )
