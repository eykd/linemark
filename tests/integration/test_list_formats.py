"""Integration tests for list output formats."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command

if TYPE_CHECKING:
    from pathlib import Path


def test_list_tree_format(tmp_path: Path) -> None:
    """Test list command outputs tree format by default."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
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

        # List in tree format (default)
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code4 == 0

        # Verify tree characters present
        assert 'Parent' in stdout4
        assert 'Child One' in stdout4
        assert 'Child Two' in stdout4
        # Tree should have indentation/box characters
        assert '├──' in stdout4 or '└──' in stdout4


def test_list_json_format(tmp_path: Path) -> None:
    """Test list command outputs valid JSON with --json flag."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Root Node',
        ])
        assert exit_code1 == 0
        root_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{root_sqid}',
        ])
        assert exit_code2 == 0

        # List in JSON format
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        assert exit_code3 == 0

        # Parse JSON output
        data = json.loads(stdout3)

        # Verify structure
        assert isinstance(data, list)
        assert len(data) == 1

        # Check root node
        root = data[0]
        assert root['title'] == 'Root Node'
        assert root['sqid'] == root_sqid
        assert 'mp' in root
        assert 'children' in root

        # Check child node
        assert len(root['children']) == 1
        child = root['children'][0]
        assert child['title'] == 'Child'
        assert 'sqid' in child


def test_list_json_preserves_hierarchy(tmp_path: Path) -> None:
    """Test JSON format preserves multi-level hierarchy."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create 3-level hierarchy
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Level 1',
        ])
        assert exit_code1 == 0
        level1_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Level 2',
            '--child-of',
            f'@{level1_sqid}',
        ])
        assert exit_code2 == 0
        level2_sqid = stdout2.split('@')[1].split(')')[0]

        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Level 3',
            '--child-of',
            f'@{level2_sqid}',
        ])
        assert exit_code3 == 0

        # Get JSON output
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        assert exit_code4 == 0

        data = json.loads(stdout4)

        # Navigate hierarchy
        assert data[0]['title'] == 'Level 1'
        assert data[0]['children'][0]['title'] == 'Level 2'
        assert data[0]['children'][0]['children'][0]['title'] == 'Level 3'


def test_list_json_with_siblings(tmp_path: Path) -> None:
    """Test JSON format with multiple siblings at same level."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with multiple children
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        for i in range(1, 4):
            exit_code_child, _stdout_child, _stderr_child = invoke_asyncclick_command([
                'lmk',
                '--directory',
                str(isolated_dir),
                'add',
                f'Child {i}',
                '--child-of',
                f'@{parent_sqid}',
            ])
            assert exit_code_child == 0

        # Get JSON output
        exit_code_json, stdout_json, _stderr_json = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        assert exit_code_json == 0

        data = json.loads(stdout_json)

        # Verify parent has 3 children
        assert len(data[0]['children']) == 3
        child_titles = [child['title'] for child in data[0]['children']]
        assert 'Child 1' in child_titles
        assert 'Child 2' in child_titles
        assert 'Child 3' in child_titles


def test_list_empty_outline(tmp_path: Path) -> None:
    """Test list command with empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # List empty outline
        exit_code, stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code == 0
        output = stdout + stderr
        assert 'No nodes found' in output


def test_list_json_empty_outline(tmp_path: Path) -> None:
    """Test list --json with empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # List empty outline as JSON
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        assert exit_code == 0
        # JSON format returns empty array for empty outline
        data = json.loads(stdout)
        assert data == []


def test_list_formats_show_same_content(tmp_path: Path) -> None:
    """Test tree and JSON formats show same nodes."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create nodes
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0

        # Get tree format
        exit_code_tree, stdout_tree, _stderr_tree = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
        ])
        assert exit_code_tree == 0

        # Get JSON format
        exit_code_json, stdout_json, _stderr_json = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        assert exit_code_json == 0

        # Both should show both chapters
        assert 'Chapter One' in stdout_tree
        assert 'Chapter Two' in stdout_tree

        data = json.loads(stdout_json)
        titles = [node['title'] for node in data]
        assert 'Chapter One' in titles
        assert 'Chapter Two' in titles
