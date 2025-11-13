"""Tests for ManageTypesUseCase implementation."""

from __future__ import annotations

from pathlib import Path

import pytest

from linemark.use_cases.manage_types import ManageTypesUseCase


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

    def create_directory(self, directory: Path) -> None:
        """Create directory (no-op for fake filesystem)."""

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]


def test_list_types_shows_all_document_types() -> None:
    """Test listing document types for a node."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node with multiple document types
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''
    fs.files[str(directory / '100_SQID1_characters_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act
    types = use_case.list_types(sqid='SQID1', directory=directory)

    # Assert
    assert len(types) == 3
    assert 'draft' in types
    assert 'notes' in types
    assert 'characters' in types


def test_list_types_returns_empty_for_nonexistent_sqid() -> None:
    """Test listing types for non-existent SQID returns empty list."""
    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act
    types = use_case.list_types(sqid='NONEXISTENT', directory=directory)

    # Assert
    assert types == []


def test_add_type_creates_new_file() -> None:
    """Test adding new document type creates file."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with required types
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act
    use_case.add_type(sqid='SQID1', doc_type='characters', directory=directory)

    # Assert - new file created
    assert str(directory / '100_SQID1_characters_chapter-one.md') in fs.files


def test_add_type_preserves_existing_files() -> None:
    """Test adding type doesn't modify existing files."""
    fs = FakeFileSystem()
    directory = Path('/test')

    draft_content = """---
title: Chapter One
---
Some content"""
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = draft_content
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = 'Notes content'

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act
    use_case.add_type(sqid='SQID1', doc_type='characters', directory=directory)

    # Assert - existing files unchanged
    assert fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] == draft_content
    assert fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] == 'Notes content'


def test_add_type_raises_error_if_type_already_exists() -> None:
    """Test adding existing type raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with draft type
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act & Assert
    with pytest.raises(ValueError, match='Type draft already exists'):
        use_case.add_type(sqid='SQID1', doc_type='draft', directory=directory)


def test_add_type_raises_error_if_sqid_not_found() -> None:
    """Test adding type to non-existent SQID raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act & Assert
    with pytest.raises(ValueError, match='Node with SQID NONEXISTENT not found'):
        use_case.add_type(sqid='NONEXISTENT', doc_type='characters', directory=directory)


def test_remove_type_deletes_file() -> None:
    """Test removing document type deletes file."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with multiple types
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''
    fs.files[str(directory / '100_SQID1_characters_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act
    use_case.remove_type(sqid='SQID1', doc_type='characters', directory=directory)

    # Assert - characters file deleted
    assert str(directory / '100_SQID1_characters_chapter-one.md') not in fs.files
    # Draft and notes preserved
    assert str(directory / '100_SQID1_draft_chapter-one.md') in fs.files
    assert str(directory / '100_SQID1_notes_chapter-one.md') in fs.files


def test_remove_type_raises_error_for_required_types() -> None:
    """Test removing required types (draft, notes) raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with required types
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act & Assert - cannot remove draft
    with pytest.raises(ValueError, match='Cannot remove required type'):
        use_case.remove_type(sqid='SQID1', doc_type='draft', directory=directory)

    # Act & Assert - cannot remove notes
    with pytest.raises(ValueError, match='Cannot remove required type'):
        use_case.remove_type(sqid='SQID1', doc_type='notes', directory=directory)


def test_remove_type_raises_error_if_type_not_found() -> None:
    """Test removing non-existent type raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with required types only
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act & Assert
    with pytest.raises(ValueError, match='Type characters not found'):
        use_case.remove_type(sqid='SQID1', doc_type='characters', directory=directory)


def test_remove_type_raises_error_if_sqid_not_found() -> None:
    """Test removing type from non-existent SQID raises ValueError."""
    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = ManageTypesUseCase(filesystem=fs)

    # Act & Assert
    with pytest.raises(ValueError, match='Node with SQID NONEXISTENT not found'):
        use_case.remove_type(sqid='NONEXISTENT', doc_type='characters', directory=directory)
