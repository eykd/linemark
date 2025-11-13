"""Integration tests for move workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_move_node_to_root(tmp_path: Path) -> None:
    """Test moving a child node to root level."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Extract parent SQID
        sqid_parent = result1.output.split('@')[1].split(')')[0]

        # Add child
        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{sqid_parent}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0

        # Extract child SQID
        sqid_child = result2.output.split('@')[1].split(')')[0]

        # Move child to root at position 200
        result3 = runner.invoke(lmk, ['move', f'@{sqid_child}', '--to', '200', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert f'Moved node @{sqid_child} to 200' in result3.output

        # Verify files were renamed
        cwd = Path.cwd()
        child_files = list(cwd.glob(f'200_{sqid_child}_*.md'))
        assert len(child_files) == 2  # draft + notes


def test_move_node_to_new_parent(tmp_path: Path) -> None:
    """Test moving node from one parent to another."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent1
        result1 = runner.invoke(lmk, ['add', 'Parent One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid_parent1 = result1.output.split('@')[1].split(')')[0]

        # Add parent2
        result2 = runner.invoke(lmk, ['add', 'Parent Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Add child to parent1
        result3 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{sqid_parent1}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0
        sqid_child = result3.output.split('@')[1].split(')')[0]

        # Move child from parent1 to parent2 (at position 200-100)
        result4 = runner.invoke(lmk, ['move', f'@{sqid_child}', '--to', '200-100', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Verify files renamed
        cwd = Path.cwd()
        child_files = list(cwd.glob(f'200-100_{sqid_child}_*.md'))
        assert len(child_files) == 2


def test_move_node_with_descendants_cascades(tmp_path: Path) -> None:
    """Test moving node with descendants updates all descendant files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid_parent = result1.output.split('@')[1].split(')')[0]

        # Add child
        result2 = runner.invoke(
            lmk, ['add', 'Child', '--child-of', f'@{sqid_parent}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0
        sqid_child = result2.output.split('@')[1].split(')')[0]

        # Add grandchild
        result3 = runner.invoke(
            lmk, ['add', 'Grandchild', '--child-of', f'@{sqid_child}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0
        sqid_grandchild = result3.output.split('@')[1].split(')')[0]

        # Move child to root at 300 (should cascade grandchild to 300-100)
        result4 = runner.invoke(lmk, ['move', f'@{sqid_child}', '--to', '300', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Verify child files at 300
        cwd = Path.cwd()
        child_files = list(cwd.glob(f'300_{sqid_child}_*.md'))
        assert len(child_files) == 2

        # Verify grandchild files cascaded to 300-100
        grandchild_files = list(cwd.glob(f'300-100_{sqid_grandchild}_*.md'))
        assert len(grandchild_files) == 2


def test_move_command_error_handling(tmp_path: Path) -> None:
    """Test move command error handling for invalid operations."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to move non-existent node
        result1 = runner.invoke(lmk, ['move', '@MISSING', '--to', '200', '--directory', str(isolated_dir)])
        assert result1.exit_code == 1
        assert 'Error' in result1.output


def test_move_preserves_content(tmp_path: Path) -> None:
    """Test moving node preserves file contents."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add node
        result1 = runner.invoke(lmk, ['add', 'My Node', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Edit draft file to add custom content
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*{sqid}_draft_*.md'))
        assert len(draft_files) == 1
        draft_file = draft_files[0]

        # Add custom content
        original_content = draft_file.read_text()
        custom_content = original_content + '\n# Custom Content\n\nSome important text.'
        draft_file.write_text(custom_content)

        # Move node
        result2 = runner.invoke(lmk, ['move', f'@{sqid}', '--to', '500', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Verify content preserved
        new_draft_files = list(cwd.glob(f'500_{sqid}_draft_*.md'))
        assert len(new_draft_files) == 1
        new_content = new_draft_files[0].read_text()
        assert 'Custom Content' in new_content
        assert 'Some important text' in new_content


def test_move_and_list_workflow(tmp_path: Path) -> None:
    """Test complete move → list workflow to verify hierarchy."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes: root1, root2, root1-child
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid1 = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        result3 = runner.invoke(
            lmk, ['add', 'Section 1.1', '--child-of', f'@{sqid1}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0
        sqid_child = result3.output.split('@')[1].split(')')[0]

        # List before move
        result4 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert 'Chapter One' in result4.output
        assert 'Section 1.1' in result4.output

        # Move Section 1.1 to root at 300
        result5 = runner.invoke(lmk, ['move', f'@{sqid_child}', '--to', '300', '--directory', str(isolated_dir)])
        assert result5.exit_code == 0

        # List after move - Section 1.1 should be at root level
        result6 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result6.exit_code == 0
        assert 'Section 1.1' in result6.output
