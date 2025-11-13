"""Integration tests for add workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_add_command_creates_root_node(tmp_path: Path) -> None:
    """Test that add command creates draft and notes files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Run add command with explicit directory
        result = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Debug output
        if result.exit_code != 0 and result.exception:
            import traceback

            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

        # Verify success
        assert result.exit_code == 0
        assert 'Created node' in result.output
        assert 'Chapter One' in result.output

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
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Add second node
        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # List nodes
        result3 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'Chapter One' in result3.output
        assert 'Chapter Two' in result3.output


def test_add_child_node_workflow(tmp_path: Path) -> None:
    """Test adding a child node to an existing node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Extract SQID from output
        lines = result1.output.split('\n')
        sqid_line = next(line for line in lines if '@' in line)
        sqid = sqid_line.split('@')[1].split(')')[0]

        # Add child node
        result2 = runner.invoke(lmk, ['add', 'Section 1.1', '--child-of', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        assert 'Section 1.1' in result2.output

        # List to verify hierarchy
        result3 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'Chapter One' in result3.output
        assert 'Section 1.1' in result3.output


def test_list_json_format(tmp_path: Path) -> None:
    """Test listing outline in JSON format."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])

        # List as JSON
        result = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        assert result.exit_code == 0

        # Verify JSON structure
        import json

        output_json = json.loads(result.output)
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
        result = runner.invoke(lmk, ['add', "Writer's Guide: Advanced!", '--directory', str(isolated_dir)])
        assert result.exit_code == 0

        # Verify file created with valid slug
        files = list(Path.cwd().glob('*_draft_*.md'))
        assert len(files) == 1
        assert 'writers-guide' in files[0].name.lower()


def test_add_multiple_levels(tmp_path: Path) -> None:
    """Test creating multi-level hierarchy."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add root
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        sqid1 = result1.output.split('@')[1].split(')')[0]

        # Add child
        result2 = runner.invoke(
            lmk, ['add', 'Section 1.1', '--child-of', f'@{sqid1}', '--directory', str(isolated_dir)]
        )
        sqid2 = result2.output.split('@')[1].split(')')[0]

        # Add grandchild
        result3 = runner.invoke(
            lmk, ['add', 'Subsection 1.1.1', '--child-of', f'@{sqid2}', '--directory', str(isolated_dir)]
        )
        assert result3.exit_code == 0

        # Verify hierarchy in list
        result4 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert 'Chapter One' in result4.output
        assert 'Section 1.1' in result4.output
        assert 'Subsection 1.1.1' in result4.output


def test_empty_directory_list(tmp_path: Path) -> None:
    """Test listing an empty directory."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        result = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result.exit_code == 0
        assert 'No nodes found' in result.output
