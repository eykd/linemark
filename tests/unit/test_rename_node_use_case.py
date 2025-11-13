"""Tests for RenameNodeUseCase implementation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from linemark.use_cases.rename_node import RenameNodeUseCase


class FakeFileSystem:
    """Fake filesystem adapter for testing."""

    def __init__(self) -> None:
        """Initialize with empty file storage."""
        self.files: dict[str, str] = {}

    def list_markdown_files(self, directory: Path) -> list[Path]:
        """List all .md files in directory."""
        return [
            Path(filepath)
            for filepath in self.files
            if filepath.startswith(str(directory)) and filepath.endswith('.md')
        ]

    def file_exists(self, filepath: Path) -> bool:
        """Check if file exists."""
        return str(filepath) in self.files

    def read_file(self, filepath: Path) -> str:
        """Read file content."""
        return self.files.get(str(filepath), '')

    def write_file(self, filepath: Path, content: str) -> None:
        """Write file content."""
        self.files[str(filepath)] = content

    def delete_file(self, filepath: Path) -> None:
        """Delete file."""
        if str(filepath) in self.files:
            del self.files[str(filepath)]

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]

    def create_directory(self, directory: Path) -> None:
        """Create directory (no-op for fake filesystem)."""


class FakeSlugifier:
    """Fake slugifier adapter for testing."""

    def slugify(self, text: str) -> str:
        """Convert text to slug."""
        return text.lower().replace(' ', '-').replace('_', '-')


def test_rename_node_updates_title_in_frontmatter() -> None:
    """Test renaming updates the title in draft file frontmatter."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node with existing title
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---

Content here
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = 'Notes content'

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act - rename to new title
    use_case.execute(sqid='SQID1', new_title='Chapter Two', directory=directory)

    # Assert - frontmatter updated
    draft_content = fs.files[str(directory / '100_SQID1_draft_chapter-two.md')]
    frontmatter = yaml.safe_load(draft_content.split('---')[1])
    assert frontmatter['title'] == 'Chapter Two'


def test_rename_node_generates_new_slug() -> None:
    """Test renaming generates new slug from new title."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node with old title
    fs.files[str(directory / '100_SQID1_draft_old-title.md')] = """---
title: Old Title
---
"""
    fs.files[str(directory / '100_SQID1_notes_old-title.md')] = ''

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act
    use_case.execute(sqid='SQID1', new_title='New Amazing Title', directory=directory)

    # Assert - new slug generated
    assert str(directory / '100_SQID1_draft_new-amazing-title.md') in fs.files
    assert str(directory / '100_SQID1_notes_new-amazing-title.md') in fs.files
    # Old files removed
    assert str(directory / '100_SQID1_draft_old-title.md') not in fs.files
    assert str(directory / '100_SQID1_notes_old-title.md') not in fs.files


def test_rename_node_renames_all_document_types() -> None:
    """Test renaming updates filenames for all document types."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node with multiple document types
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = 'Notes'
    fs.files[str(directory / '100_SQID1_characters_chapter-one.md')] = 'Characters'
    fs.files[str(directory / '100_SQID1_worldbuilding_chapter-one.md')] = 'Worldbuilding'

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act
    use_case.execute(sqid='SQID1', new_title='Chapter Two', directory=directory)

    # Assert - all files renamed
    assert str(directory / '100_SQID1_draft_chapter-two.md') in fs.files
    assert str(directory / '100_SQID1_notes_chapter-two.md') in fs.files
    assert str(directory / '100_SQID1_characters_chapter-two.md') in fs.files
    assert str(directory / '100_SQID1_worldbuilding_chapter-two.md') in fs.files
    # Old files removed
    assert str(directory / '100_SQID1_draft_chapter-one.md') not in fs.files
    assert str(directory / '100_SQID1_notes_chapter-one.md') not in fs.files


def test_rename_node_preserves_sqid() -> None:
    """Test renaming preserves the SQID in filenames."""
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.files[str(directory / '100_SQID1_draft_old-title.md')] = """---
title: Old Title
---
"""
    fs.files[str(directory / '100_SQID1_notes_old-title.md')] = ''

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act
    use_case.execute(sqid='SQID1', new_title='New Title', directory=directory)

    # Assert - SQID unchanged
    new_files = [path for path in fs.files if 'SQID1' in path]
    assert len(new_files) == 2
    assert all('SQID1' in path for path in new_files)


def test_rename_node_preserves_materialized_path() -> None:
    """Test renaming preserves the materialized path in filenames."""
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.files[str(directory / '100-200_SQID1_draft_old-title.md')] = """---
title: Old Title
---
"""
    fs.files[str(directory / '100-200_SQID1_notes_old-title.md')] = ''

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act
    use_case.execute(sqid='SQID1', new_title='New Title', directory=directory)

    # Assert - MP unchanged
    assert str(directory / '100-200_SQID1_draft_new-title.md') in fs.files
    assert str(directory / '100-200_SQID1_notes_new-title.md') in fs.files


def test_rename_node_preserves_content() -> None:
    """Test renaming preserves file content (except frontmatter title)."""
    fs = FakeFileSystem()
    directory = Path('/test')

    original_draft = """---
title: Old Title
author: Test Author
---

This is important content that must be preserved.

## Section 1

More content here.
"""
    fs.files[str(directory / '100_SQID1_draft_old-title.md')] = original_draft
    fs.files[str(directory / '100_SQID1_notes_old-title.md')] = 'Important notes'

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act
    use_case.execute(sqid='SQID1', new_title='New Title', directory=directory)

    # Assert - content preserved
    new_draft = fs.files[str(directory / '100_SQID1_draft_new-title.md')]
    assert 'This is important content that must be preserved.' in new_draft
    assert '## Section 1' in new_draft
    assert 'More content here.' in new_draft
    assert 'author: Test Author' in new_draft

    new_notes = fs.files[str(directory / '100_SQID1_notes_new-title.md')]
    assert new_notes == 'Important notes'


def test_rename_node_handles_special_characters() -> None:
    """Test renaming handles special characters in title."""
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.files[str(directory / '100_SQID1_draft_old-title.md')] = """---
title: Old Title
---
"""
    fs.files[str(directory / '100_SQID1_notes_old-title.md')] = ''

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act - title with special characters
    use_case.execute(sqid='SQID1', new_title="Chapter 1: Hero's Journey", directory=directory)

    # Assert - special characters handled in slug
    assert str(directory / "100_SQID1_draft_chapter-1:-hero's-journey.md") in fs.files
    assert str(directory / "100_SQID1_notes_chapter-1:-hero's-journey.md") in fs.files


def test_rename_node_raises_error_if_node_not_found() -> None:
    """Test renaming nonexistent node raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act & Assert
    with pytest.raises(ValueError, match='Node with SQID NONEXISTENT not found'):
        use_case.execute(sqid='NONEXISTENT', new_title='New Title', directory=directory)


def test_rename_node_with_no_title_change() -> None:
    """Test renaming to same title is a no-op."""
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    slugifier = FakeSlugifier()
    use_case = RenameNodeUseCase(filesystem=fs, slugifier=slugifier)

    # Act - rename to same title
    use_case.execute(sqid='SQID1', new_title='Chapter One', directory=directory)

    # Assert - files unchanged (same slug)
    assert str(directory / '100_SQID1_draft_chapter-one.md') in fs.files
    assert str(directory / '100_SQID1_notes_chapter-one.md') in fs.files
