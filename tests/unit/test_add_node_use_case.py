"""Unit tests for AddNodeUseCase."""

from __future__ import annotations

from pathlib import Path

from linemark.domain.entities import MaterializedPath
from linemark.use_cases.add_node import AddNodeUseCase


class FakeFileSystem:
    """Fake filesystem adapter for testing."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.directories: set[str] = set()

    def read_file(self, path: Path) -> str:
        """Read file from in-memory storage."""
        return self.files.get(str(path), '')

    def write_file(self, path: Path, content: str) -> None:
        """Write file to in-memory storage."""
        self.files[str(path)] = content

    def delete_file(self, path: Path) -> None:
        """Delete file from in-memory storage."""
        if str(path) in self.files:
            del self.files[str(path)]

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file in in-memory storage."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]

    def list_markdown_files(self, directory: Path) -> list[Path]:
        """List markdown files in directory."""
        return [Path(path) for path in self.files if path.endswith('.md') and path.startswith(str(directory))]

    def file_exists(self, path: Path) -> bool:
        """Check if file exists in in-memory storage."""
        return str(path) in self.files

    def create_directory(self, path: Path) -> None:
        """Create directory in in-memory storage."""
        self.directories.add(str(path))


class FakeSQIDGenerator:
    """Fake SQID generator for testing."""

    def __init__(self) -> None:
        self.counter = 1

    def encode(self, counter: int) -> str:
        """Generate fake SQID."""
        return f'SQID{counter}'

    def decode(self, sqid: str) -> int | None:
        """Decode fake SQID."""
        try:
            return int(sqid.replace('SQID', ''))
        except ValueError:
            return None


class FakeSlugifier:
    """Fake slugifier for testing."""

    def slugify(self, text: str) -> str:
        """Generate fake slug."""
        import re

        # Remove non-alphanumeric characters (except spaces and hyphens)
        text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with hyphens
        text = text.replace(' ', '-')
        # Convert to lowercase
        return text.lower()


def test_add_node_creates_root_node_with_draft_and_notes() -> None:
    """Test adding a root node creates draft and notes files."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act
    result = use_case.execute(title='Chapter One', directory=directory)

    # Assert
    assert len(fs.files) == 2
    assert result.sqid.value == 'SQID1'
    assert result.mp.as_string == '100'
    assert result.title == 'Chapter One'
    assert result.slug == 'chapter-one'

    # Verify draft file exists with frontmatter
    draft_filename = '100_SQID1_draft_chapter-one.md'
    assert str(Path(directory) / draft_filename) in fs.files
    draft_content = fs.files[str(Path(directory) / draft_filename)]
    assert '---' in draft_content
    assert 'title: Chapter One' in draft_content

    # Verify notes file exists
    notes_filename = '100_SQID1_notes_chapter-one.md'
    assert str(Path(directory) / notes_filename) in fs.files


def test_add_node_as_child_creates_nested_path() -> None:
    """Test adding a child node creates correct materialized path."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    # Pre-populate with parent node files
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act
    result = use_case.execute(
        title='Section 1.1',
        directory=directory,
        parent_sqid='SQID1',
    )

    # Assert
    assert result.mp.as_string == '100-100'
    assert result.mp.depth == 2
    parent_mp = MaterializedPath.from_string('100')
    assert result.mp.parent() == parent_mp


def test_add_node_increments_sqid_counter() -> None:
    """Test adding multiple nodes increments SQID counter."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act
    node1 = use_case.execute(title='Chapter One', directory=directory)
    node2 = use_case.execute(title='Chapter Two', directory=directory)
    node3 = use_case.execute(title='Chapter Three', directory=directory)

    # Assert
    assert node1.sqid.value == 'SQID1'
    assert node2.sqid.value == 'SQID2'
    assert node3.sqid.value == 'SQID3'
    assert node1.mp.as_string == '100'
    assert node2.mp.as_string == '200'
    assert node3.mp.as_string == '300'


def test_add_node_with_special_characters_in_title() -> None:
    """Test adding node with special characters creates valid slug."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act
    result = use_case.execute(title="Writer's Guide: Advanced!", directory=directory)

    # Assert
    assert result.title == "Writer's Guide: Advanced!"
    assert result.slug == 'writers-guide-advanced'


def test_add_node_loads_existing_outline_from_directory() -> None:
    """Test adding node to directory with existing nodes loads outline."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    # Pre-populate with existing node
    fs.files[str(directory / '100_SQID1_draft_chapter-one.md')] = """---
title: Chapter One
---
"""
    fs.files[str(directory / '100_SQID1_notes_chapter-one.md')] = ''

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act
    result = use_case.execute(title='Chapter Two', directory=directory)

    # Assert - should create sibling at position 200
    assert result.mp.as_string == '200'
    assert result.sqid.value == 'SQID2'


def test_add_node_respects_tiered_numbering() -> None:
    """Test adding multiple nodes uses tiered numbering (100/10/1)."""
    # Arrange
    fs = FakeFileSystem()
    sqid_gen = FakeSQIDGenerator()
    slugifier = FakeSlugifier()
    directory = Path('/test')

    use_case = AddNodeUseCase(
        filesystem=fs,
        sqid_generator=sqid_gen,
        slugifier=slugifier,
    )

    # Act - add 12 nodes to test tier transitions
    nodes = [use_case.execute(title=f'Chapter {i}', directory=directory) for i in range(1, 13)]

    # Assert tier 100 for first 9 nodes
    assert nodes[0].mp.as_string == '100'
    assert nodes[1].mp.as_string == '200'
    assert nodes[8].mp.as_string == '900'

    # Assert tier 10 after 9 nodes
    assert nodes[9].mp.as_string == '910'
    assert nodes[10].mp.as_string == '920'
    assert nodes[11].mp.as_string == '930'
