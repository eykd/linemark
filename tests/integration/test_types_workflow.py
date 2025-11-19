"""Integration tests for document types management workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_types_list_shows_default_types(tmp_path: Path) -> None:
    """Test listing types shows draft and notes by default."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # List types
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'list',
            f'@{sqid}',
        ])
        assert exit_code2 == 0
        assert 'draft' in stdout2
        assert 'notes' in stdout2


def test_types_add_creates_new_file(tmp_path: Path) -> None:
    """Test adding new document type creates file."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Add characters type
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code2 == 0
        assert 'Added type "characters"' in stdout2

        # Verify file exists
        cwd = Path.cwd()
        character_files = list(cwd.glob(f'*_{sqid}_characters_*.md'))
        assert len(character_files) == 1


def test_types_add_shows_in_list(tmp_path: Path) -> None:
    """Test added type appears in types list."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Add characters type
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code2 == 0

        # List types and verify characters is present
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'list',
            f'@{sqid}',
        ])
        assert exit_code3 == 0
        assert 'draft' in stdout3
        assert 'notes' in stdout3
        assert 'characters' in stdout3


def test_types_remove_deletes_file(tmp_path: Path) -> None:
    """Test removing type deletes file."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Add characters type
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code2 == 0

        # Remove characters type
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'remove',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code3 == 0
        assert 'Removed type "characters"' in stdout3

        # Verify file deleted
        cwd = Path.cwd()
        character_files = list(cwd.glob(f'*_{sqid}_characters_*.md'))
        assert len(character_files) == 0


def test_types_remove_preserves_draft_and_notes(tmp_path: Path) -> None:
    """Test removing custom type preserves required types."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Add characters type
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'add',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code2 == 0

        # Remove characters type
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'remove',
            'characters',
            f'@{sqid}',
        ])
        assert exit_code3 == 0

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
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Try to remove draft
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'remove',
            'draft',
            f'@{sqid}',
        ])
        assert exit_code2 != 0
        assert 'Cannot remove required type' in stdout2 or 'Cannot remove required type' in stderr2

        # Try to remove notes
        exit_code3, stdout3, stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'remove',
            'notes',
            f'@{sqid}',
        ])
        assert exit_code3 != 0
        assert 'Cannot remove required type' in stdout3 or 'Cannot remove required type' in stderr3


def test_types_read_returns_body_content(tmp_path: Path) -> None:
    """Test reading type returns body content without frontmatter."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Read draft type (should have default content)
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'read',
            'draft',
            f'@{sqid}',
        ])
        assert exit_code2 == 0
        # Should not contain frontmatter markers
        assert '---' not in stdout2 or stdout2.count('---') < 2


def test_types_read_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test reading type for nonexistent node fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to read from nonexistent node
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'read',
            'draft',
            '@NONEXIST',
        ])
        assert exit_code != 0
        assert 'Error' in stdout or 'Error' in stderr


def test_types_read_nonexistent_doctype_fails(tmp_path: Path) -> None:
    """Test reading nonexistent doctype fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Try to read nonexistent type
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'read',
            'nonexistent',
            f'@{sqid}',
        ])
        assert exit_code2 != 0
        assert 'Error' in stdout2 or 'Error' in stderr2


def test_types_write_updates_body_content(tmp_path: Path) -> None:
    """Test writing type updates body content."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Write new content to draft
        new_content = 'This is new draft content\nWith multiple lines'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=new_content
        )
        assert exit_code2 == 0

        # Read back and verify
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'types',
            'read',
            'draft',
            f'@{sqid}',
        ])
        assert exit_code3 == 0
        assert new_content in stdout3


def test_types_write_preserves_frontmatter(tmp_path: Path) -> None:
    """Test writing type preserves YAML frontmatter."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Write new content
        new_content = 'Updated content'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=new_content
        )
        assert exit_code2 == 0

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
        exit_code, stdout, stderr = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', '@NONEXIST'], stdin_content='test'
        )
        assert exit_code != 0
        assert 'Error' in stdout or 'Error' in stderr


def test_types_write_nonexistent_doctype_fails(tmp_path: Path) -> None:
    """Test writing to nonexistent doctype fails."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Try to write to nonexistent type
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'nonexistent', f'@{sqid}'], stdin_content='test'
        )
        assert exit_code2 != 0
        assert 'Error' in stdout2 or 'Error' in stderr2
