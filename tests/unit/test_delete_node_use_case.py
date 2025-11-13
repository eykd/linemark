"""Unit tests for DeleteNodeUseCase."""

from __future__ import annotations

from pathlib import Path

import pytest


class FakeFileSystem:
    """Fake filesystem adapter for testing."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def read_file(self, path: Path) -> str:
        return self.files.get(str(path), '')

    def write_file(self, path: Path, content: str) -> None:
        self.files[str(path)] = content

    def delete_file(self, path: Path) -> None:
        if str(path) in self.files:
            del self.files[str(path)]

    def list_markdown_files(self, directory: Path) -> list[Path]:
        return [Path(path) for path in self.files if path.endswith('.md') and path.startswith(str(directory))]

    def file_exists(self, path: Path) -> bool:
        return str(path) in self.files

    def create_directory(self, directory: Path) -> None:
        """Create directory (no-op for fake filesystem)."""

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]


def test_delete_leaf_node() -> None:
    """Test deleting a leaf node (no children)."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create two nodes
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '100_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '200_SQID2_draft_node-two.md')] = '---\ntitle: Node Two\n---'
    fs.files[str(directory / '200_SQID2_notes_node-two.md')] = ''

    use_case = DeleteNodeUseCase(filesystem=fs)

    # Delete leaf node
    result = use_case.execute(sqid='SQID1', directory=directory, recursive=False, promote=False)

    # Verify node deleted
    assert len(result) == 1
    assert result[0].sqid.value == 'SQID1'

    # Verify files deleted
    assert str(directory / '100_SQID1_draft_node-one.md') not in fs.files
    assert str(directory / '100_SQID1_notes_node-one.md') not in fs.files

    # Verify other node remains
    assert str(directory / '200_SQID2_draft_node-two.md') in fs.files


def test_delete_node_with_children_raises_error() -> None:
    """Test deleting node with children raises error without recursive/promote."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create parent and child
    fs.files[str(directory / '100_PARENT_draft_parent.md')] = '---\ntitle: Parent\n---'
    fs.files[str(directory / '100_PARENT_notes_parent.md')] = ''
    fs.files[str(directory / '100-100_CHILD_draft_child.md')] = '---\ntitle: Child\n---'
    fs.files[str(directory / '100-100_CHILD_notes_child.md')] = ''

    use_case = DeleteNodeUseCase(filesystem=fs)

    # Try to delete parent without flags
    with pytest.raises(ValueError, match='Cannot delete node with children'):
        use_case.execute(sqid='PARENT', directory=directory, recursive=False, promote=False)


def test_delete_recursive_removes_descendants() -> None:
    """Test recursive delete removes node and all descendants."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create parent, child, and grandchild
    fs.files[str(directory / '100_PARENT_draft_parent.md')] = '---\ntitle: Parent\n---'
    fs.files[str(directory / '100_PARENT_notes_parent.md')] = ''
    fs.files[str(directory / '100-100_CHILD_draft_child.md')] = '---\ntitle: Child\n---'
    fs.files[str(directory / '100-100_CHILD_notes_child.md')] = ''
    fs.files[str(directory / '100-100-100_GRAND_draft_grand.md')] = '---\ntitle: Grand\n---'
    fs.files[str(directory / '100-100-100_GRAND_notes_grand.md')] = ''
    fs.files[str(directory / '200_SIBLING_draft_sibling.md')] = '---\ntitle: Sibling\n---'
    fs.files[str(directory / '200_SIBLING_notes_sibling.md')] = ''

    use_case = DeleteNodeUseCase(filesystem=fs)

    # Delete parent recursively
    result = use_case.execute(sqid='PARENT', directory=directory, recursive=True, promote=False)

    # Verify all deleted
    assert len(result) == 3
    sqids = {n.sqid.value for n in result}
    assert 'PARENT' in sqids
    assert 'CHILD' in sqids
    assert 'GRAND' in sqids

    # Verify all files deleted
    assert str(directory / '100_PARENT_draft_parent.md') not in fs.files
    assert str(directory / '100-100_CHILD_draft_child.md') not in fs.files
    assert str(directory / '100-100-100_GRAND_draft_grand.md') not in fs.files

    # Verify sibling remains
    assert str(directory / '200_SIBLING_draft_sibling.md') in fs.files


def test_delete_promote_promotes_children() -> None:
    """Test promote delete promotes children to parent level."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create parent and two children
    fs.files[str(directory / '100_PARENT_draft_parent.md')] = '---\ntitle: Parent\n---'
    fs.files[str(directory / '100_PARENT_notes_parent.md')] = ''
    fs.files[str(directory / '100-100_CHILD1_draft_child1.md')] = '---\ntitle: Child 1\n---'
    fs.files[str(directory / '100-100_CHILD1_notes_child1.md')] = ''
    fs.files[str(directory / '100-200_CHILD2_draft_child2.md')] = '---\ntitle: Child 2\n---'
    fs.files[str(directory / '100-200_CHILD2_notes_child2.md')] = ''

    use_case = DeleteNodeUseCase(filesystem=fs)

    # Delete parent with promote
    result = use_case.execute(sqid='PARENT', directory=directory, recursive=False, promote=True)

    # Verify parent deleted
    assert len(result) == 1
    assert result[0].sqid.value == 'PARENT'

    # Verify parent files deleted
    assert str(directory / '100_PARENT_draft_parent.md') not in fs.files

    # Verify children promoted (files renamed to root level)
    # Children should now be at root level with new MPs
    child1_files = [p for p in fs.files if 'CHILD1' in p]
    child2_files = [p for p in fs.files if 'CHILD2' in p]
    assert len(child1_files) == 2
    assert len(child2_files) == 2

    # Children should no longer have MP starting with 100-
    for filepath in child1_files + child2_files:
        # Files should be renamed to root level (single segment MP)
        parts = Path(filepath).name.split('_')
        mp_str = parts[0]
        assert '-' not in mp_str  # Root level (single segment)


def test_delete_nonexistent_node_raises_error() -> None:
    """Test deleting nonexistent node raises error."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = DeleteNodeUseCase(filesystem=fs)

    with pytest.raises(ValueError, match='Node with SQID .* not found'):
        use_case.execute(sqid='MISSING', directory=directory, recursive=False, promote=False)


def test_recursive_and_promote_raises_error() -> None:
    """Test using both recursive and promote flags raises error."""
    from linemark.use_cases.delete_node import DeleteNodeUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = DeleteNodeUseCase(filesystem=fs)

    with pytest.raises(ValueError, match='Cannot use both recursive and promote'):
        use_case.execute(sqid='SQID1', directory=directory, recursive=True, promote=True)
