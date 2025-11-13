"""Integration tests for list output formats."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from click.testing import CliRunner

from linemark.cli.main import lmk

if TYPE_CHECKING:
    from pathlib import Path


def test_list_tree_format(tmp_path: Path) -> None:
    """Test list command outputs tree format by default."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk,
            ['add', 'Child One', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)],
        )
        assert result2.exit_code == 0

        result3 = runner.invoke(
            lmk,
            ['add', 'Child Two', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)],
        )
        assert result3.exit_code == 0

        # List in tree format (default)
        result4 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        # Verify tree characters present
        assert 'Parent' in result4.output
        assert 'Child One' in result4.output
        assert 'Child Two' in result4.output
        # Tree should have indentation/box characters
        assert '├──' in result4.output or '└──' in result4.output


def test_list_json_format(tmp_path: Path) -> None:
    """Test list command outputs valid JSON with --json flag."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
        result1 = runner.invoke(lmk, ['add', 'Root Node', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        root_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Child', '--child-of', f'@{root_sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # List in JSON format
        result3 = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # Parse JSON output
        data = json.loads(result3.output)

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
        result1 = runner.invoke(lmk, ['add', 'Level 1', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        level1_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk,
            ['add', 'Level 2', '--child-of', f'@{level1_sqid}', '--directory', str(isolated_dir)],
        )
        assert result2.exit_code == 0
        level2_sqid = result2.output.split('@')[1].split(')')[0]

        result3 = runner.invoke(
            lmk,
            ['add', 'Level 3', '--child-of', f'@{level2_sqid}', '--directory', str(isolated_dir)],
        )
        assert result3.exit_code == 0

        # Get JSON output
        result4 = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0

        data = json.loads(result4.output)

        # Navigate hierarchy
        assert data[0]['title'] == 'Level 1'
        assert data[0]['children'][0]['title'] == 'Level 2'
        assert data[0]['children'][0]['children'][0]['title'] == 'Level 3'


def test_list_json_with_siblings(tmp_path: Path) -> None:
    """Test JSON format with multiple siblings at same level."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with multiple children
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        for i in range(1, 4):
            result = runner.invoke(
                lmk,
                [
                    'add',
                    f'Child {i}',
                    '--child-of',
                    f'@{parent_sqid}',
                    '--directory',
                    str(isolated_dir),
                ],
            )
            assert result.exit_code == 0

        # Get JSON output
        result_json = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result_json.exit_code == 0

        data = json.loads(result_json.output)

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
        result = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result.exit_code == 0
        assert 'No nodes found' in result.output


def test_list_json_empty_outline(tmp_path: Path) -> None:
    """Test list --json with empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # List empty outline as JSON
        result = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result.exit_code == 0
        # JSON format returns empty array for empty outline
        data = json.loads(result.output)
        assert data == []


def test_list_formats_show_same_content(tmp_path: Path) -> None:
    """Test tree and JSON formats show same nodes."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create nodes
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Get tree format
        result_tree = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result_tree.exit_code == 0

        # Get JSON format
        result_json = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result_json.exit_code == 0

        # Both should show both chapters
        assert 'Chapter One' in result_tree.output
        assert 'Chapter Two' in result_tree.output

        data = json.loads(result_json.output)
        titles = [node['title'] for node in data]
        assert 'Chapter One' in titles
        assert 'Chapter Two' in titles
