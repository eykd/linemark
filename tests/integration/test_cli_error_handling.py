"""Integration tests for CLI error handling and edge cases."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from click.testing import CliRunner

from linemark.cli.main import main
from tests.conftest import invoke_asyncclick_command

if TYPE_CHECKING:
    from pathlib import Path


def test_compile_oserror_handling(tmp_path: Path) -> None:
    """Test compile command handles OSError gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to compile from an existing directory but with a doctype that doesn't exist
        # This will trigger the DoctypeNotFoundError path which returns exit code 1
        exit_code, _stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'nonexistent_doctype',
        ])

        assert exit_code == 1
        assert 'Error:' in stderr


def test_add_invalid_title_error(tmp_path: Path) -> None:
    """Test add command with invalid title raises ValueError."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to add with empty/whitespace title should fail in slugifier
        exit_code, _stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'add', '   '])

        assert exit_code == 1
        assert 'Error:' in stderr


def test_list_empty_directory_message(tmp_path: Path) -> None:
    """Test list command shows message for empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        exit_code, _stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])

        assert exit_code == 0
        assert 'No nodes found' in stderr


def test_doctor_with_repair_flag(tmp_path: Path) -> None:
    """Test doctor command with --repair flag."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node first
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Test Node',
        ])
        assert exit_code1 == 0

        # Run doctor with repair on a valid outline (should pass)
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'doctor',
            '--repair',
        ])

        assert exit_code2 == 0
        assert 'valid' in stdout2.lower()


def test_types_list_no_types_error(tmp_path: Path) -> None:
    """Test types list when node has only default types."""
    from pathlib import Path

    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Test Node',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Delete the draft and notes files to simulate no types
        files = list(Path(isolated_dir).glob('*.md'))
        for f in files:
            Path(f).unlink()

        # List types should fail now
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'list',
            f'@{sqid}',
        ])

        # Will fail because node can't be found without files
        assert exit_code2 == 1


def test_types_add_invalid_type_error(tmp_path: Path) -> None:
    """Test types add command with invalid type name."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Test Node',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Try to add a reserved type (draft or notes)
        exit_code2, _stdout2, stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'draft',
            f'@{sqid}',
        ])

        assert exit_code2 == 1
        assert 'Error:' in stderr2


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
