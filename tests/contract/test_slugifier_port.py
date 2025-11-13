"""Contract tests for SlugifierPort implementations.

These tests verify that any concrete implementation of SlugifierPort
follows the protocol contract correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from linemark.ports.slugifier import SlugifierPort


class TestSlugifierPortContract:
    """Contract tests for SlugifierPort protocol.

    To test an implementation, create a test class that inherits from this
    and provides a slugifier fixture.
    """

    # Mark as non-collection to avoid pytest discovering this base class
    __test__ = False

    def test_slugify_simple_text(self, slugifier: SlugifierPort) -> None:
        """Slugify simple text with spaces."""
        result = slugifier.slugify('Chapter One')

        assert result == 'chapter-one'

    def test_slugify_with_punctuation(self, slugifier: SlugifierPort) -> None:
        """Slugify text with punctuation and special characters."""
        result = slugifier.slugify("Writer's Guide: Advanced!")

        assert result == 'writers-guide-advanced'

    def test_slugify_with_unicode(self, slugifier: SlugifierPort) -> None:
        """Slugify text with unicode characters."""
        result = slugifier.slugify('Über cool')

        # Should transliterate unicode to ASCII
        assert result == 'uber-cool'

    def test_slugify_is_lowercase(self, slugifier: SlugifierPort) -> None:
        """Slugified text is lowercase."""
        result = slugifier.slugify('UPPERCASE TEXT')

        assert result == 'uppercase-text'
        assert result.islower()

    def test_slugify_is_deterministic(self, slugifier: SlugifierPort) -> None:
        """Same input produces same slug."""
        text = 'Test Chapter'
        result1 = slugifier.slugify(text)
        result2 = slugifier.slugify(text)

        assert result1 == result2

    def test_slugify_removes_multiple_spaces(self, slugifier: SlugifierPort) -> None:
        """Multiple spaces become single hyphen."""
        result = slugifier.slugify('Chapter   One')

        assert result == 'chapter-one'

    def test_slugify_trims_leading_trailing_spaces(self, slugifier: SlugifierPort) -> None:
        """Leading/trailing spaces are removed."""
        result = slugifier.slugify('  Chapter One  ')

        assert result == 'chapter-one'

    def test_slugify_alphanumeric_and_hyphens_only(self, slugifier: SlugifierPort) -> None:
        """Slug contains only alphanumeric and hyphens."""
        texts = [
            'Simple Text',
            'Complex-Text_With$Symbols!',
            'Numbers 123 and 456',
        ]

        for text in texts:
            result = slugifier.slugify(text)
            # Remove hyphens and check remaining chars are alphanumeric
            without_hyphens = result.replace('-', '')
            assert without_hyphens.isalnum(), f'Slug {result!r} contains invalid characters'

    def test_slugify_empty_string_raises_error(self, slugifier: SlugifierPort) -> None:
        """Empty string raises ValueError."""
        with pytest.raises(ValueError):
            slugifier.slugify('')

    def test_slugify_whitespace_only_raises_error(self, slugifier: SlugifierPort) -> None:
        """Whitespace-only string raises ValueError."""
        with pytest.raises(ValueError):
            slugifier.slugify('   ')

        with pytest.raises(ValueError):
            slugifier.slugify('\t\n  ')

    def test_slugify_preserves_numbers(self, slugifier: SlugifierPort) -> None:
        """Numbers are preserved in slug."""
        result = slugifier.slugify('Chapter 42 Section 3')

        assert result == 'chapter-42-section-3'

    def test_slugify_handles_consecutive_punctuation(self, slugifier: SlugifierPort) -> None:
        """Consecutive punctuation becomes single hyphen."""
        result = slugifier.slugify('Chapter... One!!!')

        # Should not have multiple consecutive hyphens
        assert '--' not in result
        assert result == 'chapter-one'

    def test_slugify_no_leading_trailing_hyphens(self, slugifier: SlugifierPort) -> None:
        """Slug has no leading or trailing hyphens."""
        texts = [
            '-Leading Hyphen',
            'Trailing Hyphen-',
            '---Multiple Leading',
            'Multiple Trailing---',
        ]

        for text in texts:
            result = slugifier.slugify(text)
            assert not result.startswith('-'), f'Slug {result!r} starts with hyphen'
            assert not result.endswith('-'), f'Slug {result!r} ends with hyphen'

    def test_slugify_only_special_characters_raises_error(self, slugifier: SlugifierPort) -> None:
        """Text with only special characters that produce empty slug raises ValueError."""
        with pytest.raises(ValueError, match='Input produced empty slug'):
            slugifier.slugify('...')
