"""Integration tests for move workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_move_node_to_root(tmp_path: Path) -> None:
    """Test moving a child node to root level."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0

        # Extract parent SQID
        sqid_parent = stdout1.split('@')[1].split(')')[0]

        # Add child
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{sqid_parent}',
        ])
        assert exit_code2 == 0

        # Extract child SQID
        sqid_child = stdout2.split('@')[1].split(')')[0]

        # Move child to root at position 200
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            f'@{sqid_child}',
            '--to',
            '200',
        ])
        assert exit_code3 == 0
        assert f'Moved node @{sqid_child} to 200' in stdout3

        # Verify files were renamed
        cwd = Path.cwd()
        child_files = list(cwd.glob(f'200_{sqid_child}_*.md'))
        assert len(child_files) == 2  # draft + notes


def test_move_node_to_new_parent(tmp_path: Path) -> None:
    """Test moving node from one parent to another."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent1
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent One',
        ])
        assert exit_code1 == 0
        sqid_parent1 = stdout1.split('@')[1].split(')')[0]

        # Add parent2
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent Two',
        ])
        assert exit_code2 == 0

        # Add child to parent1
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{sqid_parent1}',
        ])
        assert exit_code3 == 0
        sqid_child = stdout3.split('@')[1].split(')')[0]

        # Move child from parent1 to parent2 (at position 200-100)
        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            f'@{sqid_child}',
            '--to',
            '200-100',
        ])
        assert exit_code4 == 0

        # Verify files renamed
        cwd = Path.cwd()
        child_files = list(cwd.glob(f'200-100_{sqid_child}_*.md'))
        assert len(child_files) == 2


def test_move_node_with_descendants_cascades(tmp_path: Path) -> None:
    """Test moving node with descendants updates all descendant files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        sqid_parent = stdout1.split('@')[1].split(')')[0]

        # Add child
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{sqid_parent}',
        ])
        assert exit_code2 == 0
        sqid_child = stdout2.split('@')[1].split(')')[0]

        # Add grandchild
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Grandchild',
            '--child-of',
            f'@{sqid_child}',
        ])
        assert exit_code3 == 0
        sqid_grandchild = stdout3.split('@')[1].split(')')[0]

        # Move child to root at 300 (should cascade grandchild to 300-100)
        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            f'@{sqid_child}',
            '--to',
            '300',
        ])
        assert exit_code4 == 0

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
        exit_code1, stdout1, stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            '@MISSING',
            '--to',
            '200',
        ])
        assert exit_code1 == 1
        output = stdout1 + stderr1
        assert 'Error' in output


def test_move_preserves_content(tmp_path: Path) -> None:
    """Test moving node preserves file contents."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'My Node',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

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
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            f'@{sqid}',
            '--to',
            '500',
        ])
        assert exit_code2 == 0

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
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid1 = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0

        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            f'@{sqid1}',
        ])
        assert exit_code3 == 0
        sqid_child = stdout3.split('@')[1].split(')')[0]

        # List before move
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code4 == 0
        assert 'Chapter One' in stdout4
        assert 'Section 1.1' in stdout4

        # Move Section 1.1 to root at 300
        exit_code5, _stdout5, _stderr5 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'move',
            f'@{sqid_child}',
            '--to',
            '300',
        ])
        assert exit_code5 == 0

        # List after move - Section 1.1 should be at root level
        exit_code6, stdout6, _stderr6 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code6 == 0
        assert 'Section 1.1' in stdout6
