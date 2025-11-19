"""Integration tests for add workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_add_command_creates_root_node(tmp_path: Path) -> None:
    """Test that add command creates draft and notes files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Run add command with explicit directory
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Verify success
        assert exit_code == 0
        assert 'Created node' in stdout
        assert 'Chapter One' in stdout

        # Verify files were created
        cwd = Path.cwd()
        files = list(cwd.glob('*.md'))
        assert len(files) == 2  # draft + notes

        # Verify filenames match pattern
        draft_file = next(f for f in files if '_draft_' in f.name)
        notes_file = next(f for f in files if '_notes_' in f.name)

        assert draft_file.exists()
        assert notes_file.exists()

        # Verify draft has frontmatter
        draft_content = draft_file.read_text()
        assert '---' in draft_content
        assert 'title: Chapter One' in draft_content


def test_add_and_list_workflow(tmp_path: Path) -> None:
    """Test complete add → list workflow."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add first node
        exit_code1, _stdout1, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        # Add second node
        exit_code2, _stdout2, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0

        # List nodes
        exit_code3, stdout3, _ = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code3 == 0
        assert 'Chapter One' in stdout3
        assert 'Chapter Two' in stdout3


def test_add_child_node_workflow(tmp_path: Path) -> None:
    """Test adding a child node to an existing node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent node
        exit_code1, stdout1, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        # Extract SQID from output
        lines = stdout1.split('\n')
        sqid_line = next(line for line in lines if '@' in line)
        sqid = sqid_line.split('@')[1].split(')')[0]

        # Add child node
        exit_code2, stdout2, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            f'@{sqid}',
        ])
        assert exit_code2 == 0
        assert 'Section 1.1' in stdout2

        # List to verify hierarchy
        exit_code3, stdout3, _ = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code3 == 0
        assert 'Chapter One' in stdout3
        assert 'Section 1.1' in stdout3


def test_list_json_format(tmp_path: Path) -> None:
    """Test listing outline in JSON format."""
    import json

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes
        invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'add', 'Chapter One'])
        invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'add', 'Chapter Two'])

        # List as JSON
        exit_code, stdout, _ = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list', '--json'])
        assert exit_code == 0

        # Verify JSON structure
        output_json = json.loads(stdout)
        assert len(output_json) == 2
        assert output_json[0]['title'] == 'Chapter One'
        assert output_json[1]['title'] == 'Chapter Two'
        assert 'sqid' in output_json[0]
        assert 'mp' in output_json[0]


def test_add_with_special_characters(tmp_path: Path) -> None:
    """Test adding node with special characters in title."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add node with special characters
        exit_code, _stdout, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            "Writer's Guide: Advanced!",
        ])
        assert exit_code == 0

        # Verify file created with valid slug
        files = list(Path.cwd().glob('*_draft_*.md'))
        assert len(files) == 1
        assert 'writers-guide' in files[0].name.lower()


def test_add_multiple_levels(tmp_path: Path) -> None:
    """Test creating multi-level hierarchy."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add root
        _, stdout1, _ = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'add', 'Chapter One'])
        sqid1 = stdout1.split('@')[1].split(')')[0]

        # Add child
        _, stdout2, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            f'@{sqid1}',
        ])
        sqid2 = stdout2.split('@')[1].split(')')[0]

        # Add grandchild
        exit_code3, _stdout3, _ = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Subsection 1.1.1',
            '--child-of',
            f'@{sqid2}',
        ])
        assert exit_code3 == 0

        # Verify hierarchy in list
        _, stdout4, _ = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert 'Chapter One' in stdout4
        assert 'Section 1.1' in stdout4
        assert 'Subsection 1.1.1' in stdout4


def test_empty_directory_list(tmp_path: Path) -> None:
    """Test listing an empty directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        exit_code, _stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert exit_code == 0
        assert 'No nodes found' in stderr
