"""Integration tests for document types management workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_types_list_shows_default_types(tmp_path: Path) -> None:
    """Test listing types shows draft and notes by default."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # List types
        result2 = runner.invoke(lmk, ['types', 'list', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        assert 'draft' in result2.output
        assert 'notes' in result2.output


def test_types_add_creates_new_file(tmp_path: Path) -> None:
    """Test adding new document type creates file."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add characters type
        result2 = runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        assert 'Added type "characters"' in result2.output

        # Verify file exists
        cwd = Path.cwd()
        character_files = list(cwd.glob(f'*_{sqid}_characters_*.md'))
        assert len(character_files) == 1


def test_types_add_shows_in_list(tmp_path: Path) -> None:
    """Test added type appears in types list."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add characters type
        result2 = runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # List types and verify characters is present
        result3 = runner.invoke(lmk, ['types', 'list', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'draft' in result3.output
        assert 'notes' in result3.output
        assert 'characters' in result3.output


def test_types_remove_deletes_file(tmp_path: Path) -> None:
    """Test removing type deletes file."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add characters type
        result2 = runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Remove characters type
        result3 = runner.invoke(lmk, ['types', 'remove', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'Removed type "characters"' in result3.output

        # Verify file deleted
        cwd = Path.cwd()
        character_files = list(cwd.glob(f'*_{sqid}_characters_*.md'))
        assert len(character_files) == 0


def test_types_remove_preserves_draft_and_notes(tmp_path: Path) -> None:
    """Test removing custom type preserves required types."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add characters type
        result2 = runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Remove characters type
        result3 = runner.invoke(lmk, ['types', 'remove', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # Verify draft and notes still exist
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*_{sqid}_draft_*.md'))
        notes_files = list(cwd.glob(f'*_{sqid}_notes_*.md'))
        assert len(draft_files) == 1
        assert len(notes_files) == 1


def test_types_remove_required_type_fails(tmp_path: Path) -> None:
    """Test removing required types (draft, notes) fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Try to remove draft
        result2 = runner.invoke(lmk, ['types', 'remove', 'draft', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code != 0
        assert 'Cannot remove required type' in result2.output

        # Try to remove notes
        result3 = runner.invoke(lmk, ['types', 'remove', 'notes', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code != 0
        assert 'Cannot remove required type' in result3.output
