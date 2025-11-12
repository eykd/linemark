"""Slugifier Port Contract.

This module defines the abstract interface for converting titles to URL-safe slugs.
The port isolates domain logic from slug generation implementation details.

Constitutional Alignment:
- Hexagonal Architecture (§ I): Port defines boundary for slug generation
- Test-First Development (§ II): Contract enables testing with predictable fake slugifiers
"""

from __future__ import annotations

from typing import Protocol


class SlugifierPort(Protocol):
    """Port for slug generation.

    This protocol defines the contract for converting arbitrary titles into
    URL-safe, filename-safe slugs using kebab-case convention.

    Implementation Note:
        The python-slugify library handles unicode normalization, special character
        removal, and ASCII transliteration automatically.
    """

    def slugify(self, text: str) -> str:
        """Convert text to URL-safe slug.

        Args:
            text: Input string (may contain spaces, punctuation, unicode)

        Returns:
            Lowercase kebab-case slug (alphanumeric + hyphens only)

        Raises:
            ValueError: If input produces empty slug

        Example:
            >>> slugifier.slugify('Chapter One')
            'chapter-one'
            >>> slugifier.slugify("Writer's Guide: Advanced!")
            'writers-guide-advanced'
            >>> slugifier.slugify('Über cool')
            'uber-cool'

        Note:
            Same input MUST always produce same slug (deterministic).
            Empty or whitespace-only input should raise ValueError.

        """
        ...
