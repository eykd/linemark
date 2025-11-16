"""Search domain logic for pattern compilation and SQID extraction.

This module contains pure domain logic for search operations,
including regex pattern compilation and filename parsing.
"""

from __future__ import annotations

import re

from linemark.domain.exceptions import InvalidRegexError


def compile_search_pattern(
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
    if literal:
        pattern = re.escape(pattern)

    flags = 0
    if not case_sensitive:
        flags |= re.IGNORECASE
    if multiline:
        flags |= re.DOTALL

    try:
        return re.compile(pattern, flags)
    except re.error as e:
        msg = f'Invalid regex pattern: {e}'
        raise InvalidRegexError(msg) from e


def extract_sqid_from_filename(filename: str) -> str:
    """Extract SQID from a linemark filename.

    Parses the filename pattern NNN-NNN-NNN_SQID_DOCTYPE_SLUG.md
    to extract just the SQID component.

    Args:
        filename: Filename to parse

    Returns:
        SQID (without @ prefix)

    Raises:
        ValueError: If filename doesn't match expected pattern

    Examples:
        >>> extract_sqid_from_filename('100-200-300_ABC123_notes_chapter-1.md')
        'ABC123'
        >>> extract_sqid_from_filename('100_XYZ789_characters_protagonist.md')
        'XYZ789'

    """
    # Expected filename format: NNN-NNN-NNN_SQID_DOCTYPE_SLUG.md
    # Extract SQID which appears after first underscore and before second underscore
    parts = filename.split('_')
    if len(parts) < 3:  # pragma: no cover
        msg = f'Invalid filename format: {filename}'
        raise ValueError(msg)

    return parts[1]
