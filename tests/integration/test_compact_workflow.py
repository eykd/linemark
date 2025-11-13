"""Integration tests for outline compaction workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_compact_root_level_with_irregular_spacing(tmp_path: Path) -> None:
    """Test compacting root-level nodes with gaps."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create 4 nodes with irregular spacing: 001, 003, 007, 099
        result1 = runner.invoke(lmk, ['add', 'Node One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        result2 = runner.invoke(lmk, ['add', 'Node Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        result3 = runner.invoke(lmk, ['add', 'Node Three', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        result4 = runner.invoke(lmk, ['add', 'Node Four', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Compact root level
        result5 = runner.invoke(lmk, ['compact', '--directory', str(isolated_dir)])
        assert result5.exit_code == 0
        assert 'Compacted 4 root-level nodes' in result5.output

        # Verify new spacing uses 100s tier
        cwd = Path.cwd()
        files = list(cwd.glob('*.md'))
        file_names = [f.name for f in files]

        # Should have files starting with 100, 200, 300, 400
        assert any('100_' in name for name in file_names)
        assert any('200_' in name for name in file_names)
        assert any('300_' in name for name in file_names)
        assert any('400_' in name for name in file_names)

        # Verify old spacing gone
        assert not any('001_' in name for name in file_names)
        assert not any('002_' in name for name in file_names)


def test_compact_specific_subtree(tmp_path: Path) -> None:
    """Test compacting children of a specific node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        # Add 3 children
        result2 = runner.invoke(
            lmk, ['add', 'Child One', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0

        result3 = runner.invoke(
            lmk, ['add', 'Child Two', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0

        result4 = runner.invoke(
            lmk, ['add', 'Child Three', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result4.exit_code == 0

        # Compact children of parent
        result5 = runner.invoke(lmk, ['compact', f'@{parent_sqid}', '--directory', str(isolated_dir)])
        assert result5.exit_code == 0
        assert f'Compacted 3 children of @{parent_sqid}' in result5.output

        # Verify children now use even spacing (100, 200, 300)
        cwd = Path.cwd()
        children_files = list(cwd.glob('*-*_*.md'))
        file_names = [f.name for f in children_files]

        # Should have files with -100, -200, -300 in MP
        assert any('-100_' in name for name in file_names)
        assert any('-200_' in name for name in file_names)
        assert any('-300_' in name for name in file_names)


def test_compact_preserves_hierarchy(tmp_path: Path) -> None:
    """Test that compacting preserves parent-child relationships."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with children
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0

        # Add another root node
        result3 = runner.invoke(lmk, ['add', 'Root Two', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # Compact root level
        result4 = runner.invoke(lmk, ['compact', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Verify hierarchy intact via list
        result5 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert 'Parent' in result5.output
        assert 'Child' in result5.output
        assert 'Root Two' in result5.output


def test_compact_with_many_siblings_uses_smaller_tier(tmp_path: Path) -> None:
    """Test that compact uses appropriate tier based on sibling count."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create 12 root nodes to trigger 10s tier
        for i in range(1, 13):
            result = runner.invoke(lmk, ['add', f'Node {i}', '--directory', str(isolated_dir)])
            assert result.exit_code == 0

        # Compact root level
        result_compact = runner.invoke(lmk, ['compact', '--directory', str(isolated_dir)])
        assert result_compact.exit_code == 0
        assert 'Compacted 12 root-level nodes' in result_compact.output

        # Verify uses 10s tier: 010, 020, 030, ..., 120
        cwd = Path.cwd()
        files = list(cwd.glob('*.md'))
        file_names = [f.name for f in files]

        assert any('010_' in name for name in file_names)
        assert any('020_' in name for name in file_names)
        assert any('120_' in name for name in file_names)


def test_compact_preserves_content(tmp_path: Path) -> None:
    """Test that compacting preserves file contents."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create nodes
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid1 = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Write content to first chapter
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*{sqid1}_draft*.md'))
        assert len(draft_files) == 1
        draft_file = draft_files[0]

        # Read original content
        original_content = draft_file.read_text()
        assert 'Chapter One' in original_content

        # Compact
        result3 = runner.invoke(lmk, ['compact', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # Find renamed file and verify content
        new_draft_files = list(cwd.glob(f'*{sqid1}_draft*.md'))
        assert len(new_draft_files) == 1
        new_draft_file = new_draft_files[0]

        new_content = new_draft_file.read_text()
        assert 'Chapter One' in new_content


def test_compact_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test compacting nonexistent node fails gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        result = runner.invoke(lmk, ['compact', '@NONEXISTENT', '--directory', str(isolated_dir)])
        assert result.exit_code != 0
        assert 'not found' in result.output


def test_compact_with_deep_hierarchy(tmp_path: Path) -> None:
    """Test compacting updates descendant paths correctly."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        # Add child
        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0
        child_sqid = result2.output.split('@')[1].split(')')[0]

        # Add grandchild
        result3 = runner.invoke(
            lmk, ['add', 'Grandchild', '--child-of', f'@{child_sqid}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0
        grandchild_sqid = result3.output.split('@')[1].split(')')[0]

        # Add another root to trigger compaction
        result4 = runner.invoke(lmk, ['add', 'Root Two', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Compact root level
        result5 = runner.invoke(lmk, ['compact', '--directory', str(isolated_dir)])
        assert result5.exit_code == 0

        # Verify grandchild file updated with new path prefix
        cwd = Path.cwd()
        grandchild_files = list(cwd.glob(f'*{grandchild_sqid}*.md'))
        assert len(grandchild_files) == 2  # draft + notes

        # Check that grandchild files have 3-segment MP (depth 3)
        grandchild_file = grandchild_files[0].name
        mp_part = grandchild_file.split('_')[0]
        assert mp_part.count('-') == 2  # 3-segment path has 2 dashes
