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


def test_types_read_returns_body_content(tmp_path: Path) -> None:
    """Test reading type returns body content without frontmatter."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Read draft type (should have default content)
        result2 = runner.invoke(lmk, ['types', 'read', 'draft', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        # Should not contain frontmatter markers
        assert '---' not in result2.output or result2.output.count('---') < 2


def test_types_read_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test reading type for nonexistent node fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to read from nonexistent node
        result = runner.invoke(lmk, ['types', 'read', 'draft', '@NONEXIST', '--directory', str(isolated_dir)])
        assert result.exit_code != 0
        assert 'Error' in result.output


def test_types_read_nonexistent_doctype_fails(tmp_path: Path) -> None:
    """Test reading nonexistent doctype fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Try to read nonexistent type
        result2 = runner.invoke(lmk, ['types', 'read', 'nonexistent', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code != 0
        assert 'Error' in result2.output


def test_types_write_updates_body_content(tmp_path: Path) -> None:
    """Test writing type updates body content."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write new content to draft
        new_content = 'This is new draft content\nWith multiple lines'
        result2 = runner.invoke(
            lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=new_content
        )
        assert result2.exit_code == 0

        # Read back and verify
        result3 = runner.invoke(lmk, ['types', 'read', 'draft', f'@{sqid}', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert new_content in result3.output


def test_types_write_preserves_frontmatter(tmp_path: Path) -> None:
    """Test writing type preserves YAML frontmatter."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write new content
        new_content = 'Updated content'
        result2 = runner.invoke(
            lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=new_content
        )
        assert result2.exit_code == 0

        # Read the file directly and verify frontmatter is preserved
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*_{sqid}_draft_*.md'))
        assert len(draft_files) == 1
        content = draft_files[0].read_text()
        assert content.startswith('---\n')
        assert 'title:' in content
        assert new_content in content


def test_types_write_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test writing to nonexistent node fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to write to nonexistent node
        result = runner.invoke(
            lmk, ['types', 'write', 'draft', '@NONEXIST', '--directory', str(isolated_dir)], input='test'
        )
        assert result.exit_code != 0
        assert 'Error' in result.output


def test_types_write_nonexistent_doctype_fails(tmp_path: Path) -> None:
    """Test writing to nonexistent doctype fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Try to write to nonexistent type
        result2 = runner.invoke(
            lmk, ['types', 'write', 'nonexistent', f'@{sqid}', '--directory', str(isolated_dir)], input='test'
        )
        assert result2.exit_code != 0
        assert 'Error' in result2.output
