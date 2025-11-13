"""Unit tests for MoveNodeUseCase."""

from __future__ import annotations

from pathlib import Path


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


def test_move_node_to_new_parent_renames_files() -> None:
    """Test moving node to new parent renames all document files."""
    # Arrange
    from linemark.use_cases.move_node import MoveNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with nodes: 100 (parent1), 200 (parent2), 100-100 (child)
    fs.files[str(directory / '100_SQID1_draft_parent-one.md')] = """---
title: Parent One
---
"""
    fs.files[str(directory / '100_SQID1_notes_parent-one.md')] = ''
    fs.files[str(directory / '200_SQID2_draft_parent-two.md')] = """---
title: Parent Two
---
"""
    fs.files[str(directory / '200_SQID2_notes_parent-two.md')] = ''
    fs.files[str(directory / '100-100_SQID3_draft_child.md')] = """---
title: Child
---
"""
    fs.files[str(directory / '100-100_SQID3_notes_child.md')] = ''

    use_case = MoveNodeUseCase(filesystem=fs)

    # Act - move child from 100-100 to 200-100
    use_case.execute(
        sqid='SQID3',
        new_mp_str='200-100',
        directory=directory,
    )

    # Assert - child files renamed
    assert str(directory / '200-100_SQID3_draft_child.md') in fs.files
    assert str(directory / '200-100_SQID3_notes_child.md') in fs.files
    assert str(directory / '100-100_SQID3_draft_child.md') not in fs.files
    assert str(directory / '100-100_SQID3_notes_child.md') not in fs.files

    # Parent files unchanged
    assert str(directory / '100_SQID1_draft_parent-one.md') in fs.files
    assert str(directory / '200_SQID2_draft_parent-two.md') in fs.files


def test_move_node_with_descendants_cascades_renames() -> None:
    """Test moving node with descendants renames all descendant files."""
    # Arrange
    from linemark.use_cases.move_node import MoveNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with hierarchy: 100-100 (child), 100-100-100 (grandchild)
    fs.files[str(directory / '100_SQID1_draft_root.md')] = """---
title: Root
---
"""
    fs.files[str(directory / '100_SQID1_notes_root.md')] = ''
    fs.files[str(directory / '100-100_SQID2_draft_child.md')] = """---
title: Child
---
"""
    fs.files[str(directory / '100-100_SQID2_notes_child.md')] = ''
    fs.files[str(directory / '100-100-100_SQID3_draft_grandchild.md')] = """---
title: Grandchild
---
"""
    fs.files[str(directory / '100-100-100_SQID3_notes_grandchild.md')] = ''

    use_case = MoveNodeUseCase(filesystem=fs)

    # Act - move child (100-100) to root as 200
    use_case.execute(
        sqid='SQID2',
        new_mp_str='200',
        directory=directory,
    )

    # Assert - child renamed to 200
    assert str(directory / '200_SQID2_draft_child.md') in fs.files
    assert str(directory / '200_SQID2_notes_child.md') in fs.files

    # Assert - grandchild cascaded to 200-100
    assert str(directory / '200-100_SQID3_draft_grandchild.md') in fs.files
    assert str(directory / '200-100_SQID3_notes_grandchild.md') in fs.files

    # Old files removed
    assert str(directory / '100-100_SQID2_draft_child.md') not in fs.files
    assert str(directory / '100-100-100_SQID3_draft_grandchild.md') not in fs.files


def test_move_node_sqid_not_found_raises_error() -> None:
    """Test moving non-existent node raises error."""
    # Arrange
    from linemark.use_cases.move_node import MoveNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = MoveNodeUseCase(filesystem=fs)

    # Act & Assert
    import pytest

    with pytest.raises(ValueError, match='Node with SQID .* not found'):
        use_case.execute(
            sqid='MISSING',
            new_mp_str='200',
            directory=directory,
        )


def test_move_node_target_position_occupied_raises_error() -> None:
    """Test moving to occupied position raises error."""
    # Arrange
    from linemark.use_cases.move_node import MoveNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Pre-populate with two nodes at 100 and 200
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = """---
title: Node One
---
"""
    fs.files[str(directory / '100_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '200_SQID2_draft_node-two.md')] = """---
title: Node Two
---
"""
    fs.files[str(directory / '200_SQID2_notes_node-two.md')] = ''

    use_case = MoveNodeUseCase(filesystem=fs)

    # Act & Assert - try to move SQID1 to 200 (occupied by SQID2)
    import pytest

    with pytest.raises(ValueError, match='Target path .* already occupied'):
        use_case.execute(
            sqid='SQID1',
            new_mp_str='200',
            directory=directory,
        )


def test_move_node_preserves_file_contents() -> None:
    """Test moving node preserves draft content."""
    # Arrange
    from linemark.use_cases.move_node import MoveNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    original_content = """---
title: My Chapter
author: Test Author
---

# My Chapter

Some important content here.
"""

    # Pre-populate with node
    fs.files[str(directory / '100_SQID1_draft_my-chapter.md')] = original_content
    fs.files[str(directory / '100_SQID1_notes_my-chapter.md')] = 'Some notes'

    use_case = MoveNodeUseCase(filesystem=fs)

    # Act - move to 200
    use_case.execute(
        sqid='SQID1',
        new_mp_str='200',
        directory=directory,
    )

    # Assert - content preserved
    assert fs.files[str(directory / '200_SQID1_draft_my-chapter.md')] == original_content
    assert fs.files[str(directory / '200_SQID1_notes_my-chapter.md')] == 'Some notes'
