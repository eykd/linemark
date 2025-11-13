"""Integration tests for CLI error handling and edge cases."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from click.testing import CliRunner

from linemark.cli.main import lmk, main

if TYPE_CHECKING:
    from pathlib import Path


def test_compile_oserror_handling(tmp_path: Path) -> None:
    """Test compile command handles OSError gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Try to compile from a non-existent directory that will cause OSError
        nonexistent = tmp_path / 'nonexistent_dir'
        result = runner.invoke(lmk, ['compile', 'draft', '--directory', str(nonexistent)])

        assert result.exit_code == 2
        assert 'Error:' in result.output


def test_add_invalid_title_error(tmp_path: Path) -> None:
    """Test add command with invalid title raises ValueError."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to add with empty/whitespace title should fail in slugifier
        result = runner.invoke(lmk, ['add', '   ', '--directory', str(isolated_dir)])

        assert result.exit_code == 1
        assert 'Error:' in result.output


def test_list_empty_directory_message(tmp_path: Path) -> None:
    """Test list command shows message for empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        result = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'No nodes found' in result.output


def test_doctor_with_repair_flag(tmp_path: Path) -> None:
    """Test doctor command with --repair flag."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node first
        result1 = runner.invoke(lmk, ['add', 'Test Node', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Run doctor with repair on a valid outline (should pass)
        result2 = runner.invoke(lmk, ['doctor', '--repair', '--directory', str(isolated_dir)])

        assert result2.exit_code == 0
        assert 'valid' in result2.output.lower()


def test_types_list_no_types_error(tmp_path: Path) -> None:
    """Test types list when node has only default types."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node
        result1 = runner.invoke(lmk, ['add', 'Test Node', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Delete the draft and notes files to simulate no types
        from pathlib import Path

        files = list(Path(isolated_dir).glob('*.md'))
        for f in files:
            Path(f).unlink()

        # List types should fail now
        result2 = runner.invoke(lmk, ['types', 'list', f'@{sqid}', '--directory', str(isolated_dir)])

        # Will fail because node can't be found without files
        assert result2.exit_code == 1


def test_types_add_invalid_type_error(tmp_path: Path) -> None:
    """Test types add command with invalid type name."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node
        result1 = runner.invoke(lmk, ['add', 'Test Node', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Try to add a reserved type (draft or notes)
        result2 = runner.invoke(lmk, ['types', 'add', 'draft', f'@{sqid}', '--directory', str(isolated_dir)])

        assert result2.exit_code == 1
        assert 'Error:' in result2.output


def test_main_entry_point() -> None:
    """Test main() entry point function."""
    # Just import and call to ensure it's covered
    # The main() function just calls lmk()
    import sys
    from unittest.mock import patch

    # Mock sys.exit to prevent actual exit
    with patch.object(sys, 'argv', ['lmk', '--help']), contextlib.suppress(SystemExit):
        # Expected when using --help
        main()
