"""Integration tests for node deletion workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_delete_leaf_node(tmp_path: Path) -> None:
    """Test deleting a leaf node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add two nodes
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node One',
        ])
        assert exit_code1 == 0
        sqid1 = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node Two',
        ])
        assert exit_code2 == 0

        # Delete first node
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            f'@{sqid1}',
        ])
        assert exit_code3 == 0
        assert f'Deleted node @{sqid1}' in stdout3

        # Verify node deleted (list should only show Node Two)
        _exit_code4, stdout4, _stderr4 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert 'Node Two' in stdout4
        assert 'Node One' not in stdout4

        # Verify files deleted
        cwd = Path.cwd()
        files = list(cwd.glob(f'*{sqid1}*.md'))
        assert len(files) == 0


def test_delete_node_with_children_fails(tmp_path: Path) -> None:
    """Test deleting node with children fails without flags."""
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
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0

        # Try to delete parent without flags
        exit_code3, stdout3, stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            f'@{parent_sqid}',
        ])
        assert exit_code3 != 0
        output = stdout3 + stderr3
        assert 'Cannot delete node with children' in output


def test_delete_recursive(tmp_path: Path) -> None:
    """Test recursive deletion of node and descendants."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy: parent -> child -> grandchild
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0
        child_sqid = stdout2.split('@')[1].split(')')[0]

        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Grandchild',
            '--child-of',
            f'@{child_sqid}',
        ])
        assert exit_code3 == 0

        # Add sibling to parent
        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Sibling',
        ])
        assert exit_code4 == 0

        # Delete parent recursively
        exit_code5, stdout5, _stderr5 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            f'@{parent_sqid}',
            '-r',
        ])
        assert exit_code5 == 0
        assert f'Deleted node @{parent_sqid} and 2 descendants' in stdout5

        # Verify only sibling remains
        _exit_code6, stdout6, _stderr6 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert 'Sibling' in stdout6
        assert 'Parent' not in stdout6
        assert 'Child' not in stdout6
        assert 'Grandchild' not in stdout6


def test_delete_promote(tmp_path: Path) -> None:
    """Test deleting node and promoting children."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with two children
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child One',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0

        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child Two',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code3 == 0

        # Delete parent with promote
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            f'@{parent_sqid}',
            '-p',
        ])
        assert exit_code4 == 0
        assert f'Deleted node @{parent_sqid} (children promoted to parent level)' in stdout4

        # Verify children still exist at root level
        _exit_code5, stdout5, _stderr5 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert 'Child One' in stdout5
        assert 'Child Two' in stdout5
        assert 'Parent' not in stdout5


def test_delete_with_multiple_document_types(tmp_path: Path) -> None:
    """Test deletion removes all document type files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Add custom document types
        invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'types', 'add', 'characters', f'@{sqid}'])
        invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'worldbuilding',
            f'@{sqid}',
        ])

        # Verify files exist
        cwd = Path.cwd()
        files_before = list(cwd.glob(f'*{sqid}*.md'))
        assert len(files_before) == 4  # draft, notes, characters, worldbuilding

        # Delete node
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            f'@{sqid}',
        ])
        assert exit_code2 == 0

        # Verify all files deleted
        files_after = list(cwd.glob(f'*{sqid}*.md'))
        assert len(files_after) == 0


def test_delete_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test deleting nonexistent node fails gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'delete',
            '@NONEXISTENT',
        ])
        assert exit_code != 0
        output = stdout + stderr
        assert 'not found' in output
