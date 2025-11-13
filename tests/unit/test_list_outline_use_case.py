"""Unit tests for ListOutlineUseCase."""

from __future__ import annotations

from pathlib import Path

from linemark.use_cases.list_outline import ListOutlineUseCase


class FakeFileSystem:
    """Fake filesystem adapter for testing."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def read_file(self, path: Path) -> str:
        """Read file from in-memory storage."""
        return self.files.get(str(path), '')

    def list_markdown_files(self, directory: Path) -> list[Path]:
        """List markdown files in directory."""
        return [Path(path) for path in self.files if path.endswith('.md') and path.startswith(str(directory))]

    def write_file(self, path: Path, content: str) -> None:
        """Write file to in-memory storage."""
        self.files[str(path)] = content

    def delete_file(self, path: Path) -> None:
        """Delete file from in-memory storage."""
        if str(path) in self.files:
            del self.files[str(path)]

    def file_exists(self, path: Path) -> bool:
        """Check if file exists."""
        return str(path) in self.files

    def create_directory(self, directory: Path) -> None:
        """Create directory (no-op for fake filesystem)."""

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]


def test_list_outline_returns_empty_for_empty_directory() -> None:
    """Test listing an empty directory returns empty outline."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert
    assert nodes == []


def test_list_outline_returns_single_root_node() -> None:
    """Test listing directory with single node."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert
    assert len(nodes) == 1
    assert nodes[0].title == 'Chapter One'
    assert nodes[0].sqid.value == 'SQID1'
    assert nodes[0].mp.as_string == '100'


def test_list_outline_returns_nodes_sorted_by_path() -> None:
    """Test listing returns nodes sorted lexicographically by materialized path."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes out of order
    fs.files[str(directory / '200_SQID2_draft_chapter-two.md')] = """---
title: Chapter Two
---
"""
    fs.files[str(directory / '200_SQID2_notes_chapter-two.md')] = ''

    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    fs.files[str(directory / '300_SQID3_draft_chapter-three.md')] = """---
title: Chapter Three
---
"""
    fs.files[str(directory / '300_SQID3_notes_chapter-three.md')] = ''

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert
    assert len(nodes) == 3
    assert nodes[0].title == 'Chapter One'
    assert nodes[1].title == 'Chapter Two'
    assert nodes[2].title == 'Chapter Three'


def test_list_outline_handles_hierarchical_nodes() -> None:
    """Test listing handles parent-child relationships correctly."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Root node
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    # Child node
    fs.files[str(directory / '100-100_SQID2_draft_section-1-1.md')] = """---
title: Section 1.1
---
"""
    fs.files[str(directory / '100-100_SQID2_notes_section-1-1.md')] = ''

    # Grandchild node
    fs.files[str(directory / '100-100-100_SQID3_draft_subsection-1-1-1.md')] = """---
title: Subsection 1.1.1
---
"""
    fs.files[str(directory / '100-100-100_SQID3_notes_subsection-1-1-1.md')] = ''

    # Another root node
    fs.files[str(directory / '200_SQID4_draft_chapter-two.md')] = """---
title: Chapter Two
---
"""
    fs.files[str(directory / '200_SQID4_notes_chapter-two.md')] = ''

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert
    assert len(nodes) == 4
    # Verify lexicographic ordering
    assert nodes[0].mp.as_string == '100'
    assert nodes[1].mp.as_string == '100-100'
    assert nodes[2].mp.as_string == '100-100-100'
    assert nodes[3].mp.as_string == '200'


def test_list_outline_skips_invalid_filenames() -> None:
    """Test listing skips files that don't match the filename pattern."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Valid node
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    # Invalid filenames
    fs.files[str(directory / 'README.md')] = 'Some readme content'
    fs.files[str(directory / 'invalid-filename.md')] = 'Invalid'
    fs.files[str(directory / '001_SQID2.md')] = 'Missing parts'

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert - should only return the valid node
    assert len(nodes) == 1
    assert nodes[0].title == 'Chapter One'


def test_list_outline_groups_document_types_by_node() -> None:
    """Test listing groups multiple document types for same node."""
    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Node with custom document type
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''
    fs.files[str(directory / '100_SQID1_characters_chapter-one.md')] = '# Characters'

    use_case = ListOutlineUseCase(filesystem=fs)

    # Act
    nodes = use_case.execute(directory=directory)

    # Assert
    assert len(nodes) == 1
    assert nodes[0].title == 'Chapter One'
    assert 'draft' in nodes[0].document_types
    assert 'notes' in nodes[0].document_types
    assert 'characters' in nodes[0].document_types
