"""Unit tests for CompactOutlineUseCase."""

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


def test_compact_root_level_with_irregular_spacing() -> None:
    """Test compacting root-level nodes with gaps."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes with irregular spacing: 001, 003, 007, 099
    fs.files[str(directory / '001_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '001_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '003_SQID2_draft_node-two.md')] = '---\ntitle: Node Two\n---'
    fs.files[str(directory / '003_SQID2_notes_node-two.md')] = ''
    fs.files[str(directory / '007_SQID3_draft_node-three.md')] = '---\ntitle: Node Three\n---'
    fs.files[str(directory / '007_SQID3_notes_node-three.md')] = ''
    fs.files[str(directory / '099_SQID4_draft_node-four.md')] = '---\ntitle: Node Four\n---'
    fs.files[str(directory / '099_SQID4_notes_node-four.md')] = ''

    use_case = CompactOutlineUseCase(filesystem=fs)

    # Compact root level (no parent SQID)
    result = use_case.execute(sqid=None, directory=directory)

    # Verify 4 nodes renamed
    assert len(result) == 4

    # Verify new spacing uses 100s tier (4 nodes <= 9)
    # Should be: 100, 200, 300, 400
    assert str(directory / '100_SQID1_draft_node-one.md') in fs.files
    assert str(directory / '200_SQID2_draft_node-two.md') in fs.files
    assert str(directory / '300_SQID3_draft_node-three.md') in fs.files
    assert str(directory / '400_SQID4_draft_node-four.md') in fs.files

    # Verify old files deleted
    assert str(directory / '001_SQID1_draft_node-one.md') not in fs.files
    assert str(directory / '003_SQID2_draft_node-two.md') not in fs.files


def test_compact_specific_subtree() -> None:
    """Test compacting children of a specific node."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create parent with children at irregular spacing
    fs.files[str(directory / '100_PARENT_draft_parent.md')] = '---\ntitle: Parent\n---'
    fs.files[str(directory / '100_PARENT_notes_parent.md')] = ''
    fs.files[str(directory / '100-003_CHILD1_draft_child1.md')] = '---\ntitle: Child 1\n---'
    fs.files[str(directory / '100-003_CHILD1_notes_child1.md')] = ''
    fs.files[str(directory / '100-050_CHILD2_draft_child2.md')] = '---\ntitle: Child 2\n---'
    fs.files[str(directory / '100-050_CHILD2_notes_child2.md')] = ''
    fs.files[str(directory / '100-099_CHILD3_draft_child3.md')] = '---\ntitle: Child 3\n---'
    fs.files[str(directory / '100-099_CHILD3_notes_child3.md')] = ''

    use_case = CompactOutlineUseCase(filesystem=fs)

    # Compact children of PARENT
    result = use_case.execute(sqid='PARENT', directory=directory)

    # Verify 3 children renamed
    assert len(result) == 3

    # Verify new spacing: 100-100, 100-200, 100-300
    assert str(directory / '100-100_CHILD1_draft_child1.md') in fs.files
    assert str(directory / '100-200_CHILD2_draft_child2.md') in fs.files
    assert str(directory / '100-300_CHILD3_draft_child3.md') in fs.files

    # Verify parent unchanged
    assert str(directory / '100_PARENT_draft_parent.md') in fs.files


def test_compact_uses_10s_tier_for_medium_count() -> None:
    """Test that 10s tier is used for 10-99 siblings."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create 12 nodes to trigger 10s tier
    for i in range(1, 13):
        sqid = f'SQID{i:02d}'
        mp = f'{i:03d}'
        fs.files[str(directory / f'{mp}_{sqid}_draft_node-{i}.md')] = f'---\ntitle: Node {i}\n---'
        fs.files[str(directory / f'{mp}_{sqid}_notes_node-{i}.md')] = ''

    use_case = CompactOutlineUseCase(filesystem=fs)

    result = use_case.execute(sqid=None, directory=directory)

    # Verify 12 nodes renamed
    assert len(result) == 12

    # Verify new spacing uses 10s tier: 010, 020, 030, ..., 120
    assert str(directory / '010_SQID01_draft_node-1.md') in fs.files
    assert str(directory / '020_SQID02_draft_node-2.md') in fs.files
    assert str(directory / '120_SQID12_draft_node-12.md') in fs.files


def test_compact_uses_1s_tier_for_large_count() -> None:
    """Test that 1s tier is used for 100+ siblings."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create 105 nodes to trigger 1s tier
    for i in range(1, 106):
        sqid = f'SQID{i:03d}'
        mp = f'{i:03d}'
        fs.files[str(directory / f'{mp}_{sqid}_draft_node-{i}.md')] = f'---\ntitle: Node {i}\n---'
        fs.files[str(directory / f'{mp}_{sqid}_notes_node-{i}.md')] = ''

    use_case = CompactOutlineUseCase(filesystem=fs)

    result = use_case.execute(sqid=None, directory=directory)

    # Verify 105 nodes renamed
    assert len(result) == 105

    # Verify new spacing uses 1s tier: 001, 002, 003, ..., 105
    assert str(directory / '001_SQID001_draft_node-1.md') in fs.files
    assert str(directory / '002_SQID002_draft_node-2.md') in fs.files
    assert str(directory / '105_SQID105_draft_node-105.md') in fs.files


def test_compact_preserves_hierarchy() -> None:
    """Test that compacting one level doesn't affect other levels."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create multi-level hierarchy
    fs.files[str(directory / '001_ROOT1_draft_root1.md')] = '---\ntitle: Root 1\n---'
    fs.files[str(directory / '001_ROOT1_notes_root1.md')] = ''
    fs.files[str(directory / '001-003_CHILD1_draft_child1.md')] = '---\ntitle: Child 1\n---'
    fs.files[str(directory / '001-003_CHILD1_notes_child1.md')] = ''
    fs.files[str(directory / '001-050_CHILD2_draft_child2.md')] = '---\ntitle: Child 2\n---'
    fs.files[str(directory / '001-050_CHILD2_notes_child2.md')] = ''
    fs.files[str(directory / '099_ROOT2_draft_root2.md')] = '---\ntitle: Root 2\n---'
    fs.files[str(directory / '099_ROOT2_notes_root2.md')] = ''

    use_case = CompactOutlineUseCase(filesystem=fs)

    # Compact root level only
    result = use_case.execute(sqid=None, directory=directory)

    # Verify 2 root nodes renamed
    assert len(result) == 2

    # Verify root level compacted to 100, 200
    assert str(directory / '100_ROOT1_draft_root1.md') in fs.files
    assert str(directory / '200_ROOT2_draft_root2.md') in fs.files

    # Verify children unchanged (still under 001 prefix, not 100)
    # Note: Children should be moved to match new parent MP
    # Actually, this needs clarification - should compact cascade or not?
    # Let's assume it cascades to update child MPs
    assert str(directory / '100-003_CHILD1_draft_child1.md') in fs.files
    assert str(directory / '100-050_CHILD2_draft_child2.md') in fs.files


def test_compact_nonexistent_sqid_raises_error() -> None:
    """Test compacting nonexistent node raises error."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = CompactOutlineUseCase(filesystem=fs)

    with pytest.raises(ValueError, match='Node with SQID .* not found'):
        use_case.execute(sqid='MISSING', directory=directory)


def test_compact_preserves_file_contents() -> None:
    """Test that compacting preserves file contents."""
    from linemark.use_cases.compact_outline import CompactOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes with specific content
    draft_content = '---\ntitle: Important Chapter\n---\nThis is important content.'
    notes_content = 'Research notes here.'

    fs.files[str(directory / '001_SQID1_draft_chapter.md')] = draft_content
    fs.files[str(directory / '001_SQID1_notes_chapter.md')] = notes_content
    fs.files[str(directory / '099_SQID2_draft_section.md')] = '---\ntitle: Section\n---\nSection content.'
    fs.files[str(directory / '099_SQID2_notes_section.md')] = 'Section notes.'

    use_case = CompactOutlineUseCase(filesystem=fs)

    use_case.execute(sqid=None, directory=directory)

    # Verify content preserved in renamed files
    assert fs.files[str(directory / '100_SQID1_draft_chapter.md')] == draft_content
    assert fs.files[str(directory / '100_SQID1_notes_chapter.md')] == notes_content
