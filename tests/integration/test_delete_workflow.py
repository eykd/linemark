"""Integration tests for node deletion workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_delete_leaf_node(tmp_path: Path) -> None:
    """Test deleting a leaf node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add two nodes
        result1 = runner.invoke(lmk, ['add', 'Node One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid1 = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Node Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Delete first node
        result3 = runner.invoke(lmk, ['delete', f'@{sqid1}', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert f'Deleted node @{sqid1}' in result3.output

        # Verify node deleted (list should only show Node Two)
        result4 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert 'Node Two' in result4.output
        assert 'Node One' not in result4.output

        # Verify files deleted
        cwd = Path.cwd()
        files = list(cwd.glob(f'*{sqid1}*.md'))
        assert len(files) == 0


def test_delete_node_with_children_fails(tmp_path: Path) -> None:
    """Test deleting node with children fails without flags."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0

        # Try to delete parent without flags
        result3 = runner.invoke(lmk, ['delete', f'@{parent_sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code != 0
        assert 'Cannot delete node with children' in result3.output


def test_delete_recursive(tmp_path: Path) -> None:
    """Test recursive deletion of node and descendants."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy: parent -> child -> grandchild
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0
        child_sqid = result2.output.split('@')[1].split(')')[0]

        result3 = runner.invoke(
            lmk, ['add', 'Grandchild', '--child-of', f'@{child_sqid}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0

        # Add sibling to parent
        result4 = runner.invoke(lmk, ['add', 'Sibling', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Delete parent recursively
        result5 = runner.invoke(lmk, ['delete', f'@{parent_sqid}', '-r', '--directory', str(isolated_dir)])
        assert result5.exit_code == 0
        assert f'Deleted node @{parent_sqid} and 2 descendants' in result5.output

        # Verify only sibling remains
        result6 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert 'Sibling' in result6.output
        assert 'Parent' not in result6.output
        assert 'Child' not in result6.output
        assert 'Grandchild' not in result6.output


def test_delete_promote(tmp_path: Path) -> None:
    """Test deleting node and promoting children."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with two children
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk, ['add', 'Child One', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0

        result3 = runner.invoke(
            lmk, ['add', 'Child Two', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0

        # Delete parent with promote
        result4 = runner.invoke(lmk, ['delete', f'@{parent_sqid}', '-p', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert f'Deleted node @{parent_sqid} (children promoted to parent level)' in result4.output

        # Verify children still exist at root level
        result5 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert 'Child One' in result5.output
        assert 'Child Two' in result5.output
        assert 'Parent' not in result5.output


def test_delete_with_multiple_document_types(tmp_path: Path) -> None:
    """Test deletion removes all document type files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add node
        result1 = runner.invoke(lmk, ['add', 'Chapter', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add custom document types
        runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['types', 'add', 'worldbuilding', f'@{sqid}', '--directory', str(isolated_dir)])

        # Verify files exist
        cwd = Path.cwd()
        files_before = list(cwd.glob(f'*{sqid}*.md'))
        assert len(files_before) == 4  # draft, notes, characters, worldbuilding

        # Delete node
        result2 = runner.invoke(lmk, ['delete', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Verify all files deleted
        files_after = list(cwd.glob(f'*{sqid}*.md'))
        assert len(files_after) == 0


def test_delete_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test deleting nonexistent node fails gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        result = runner.invoke(lmk, ['delete', '@NONEXISTENT', '--directory', str(isolated_dir)])
        assert result.exit_code != 0
        assert 'not found' in result.output
