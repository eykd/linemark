"""Slugifier adapter implementation.

Concrete implementation of SlugifierPort using python-slugify library.
"""

from __future__ import annotations

from slugify import slugify as python_slugify


class SlugifierAdapter:
    """Concrete slugifier using python-slugify library.

    Implements SlugifierPort protocol using the python-slugify library
    for converting titles to URL-safe, filename-safe slugs.
    """

    def slugify(self, text: str) -> str:  # noqa: PLR6301
        """Convert text to URL-safe slug.

        Args:
            text: Input string (may contain spaces, punctuation, unicode)

        Returns:
            Lowercase kebab-case slug (alphanumeric + hyphens only)

        Raises:
            ValueError: If input produces empty slug

        """
        if not text or not text.strip():
            msg = 'Cannot slugify empty or whitespace-only text'
            raise ValueError(msg)

        # Replace apostrophes with empty string before slugifying to avoid "writer-s"
        text_preprocessed = text.replace("'", '')
        slug = python_slugify(text_preprocessed, lowercase=True, separator='-')

        if not slug:
            msg = f'Input produced empty slug: {text!r}'
            raise ValueError(msg)

        return slug
