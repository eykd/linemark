"""Integration tests for node rename workflow."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from linemark.cli.main import lmk


def test_rename_updates_title_and_filenames(tmp_path: Path) -> None:
    """Test renaming updates both title and filenames."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Rename the node
        result2 = runner.invoke(lmk, ['rename', f'@{sqid}', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        assert 'Renamed node' in result2.output
        assert 'Chapter Two' in result2.output

        # Verify new files exist
        cwd = Path.cwd()
        new_draft_files = list(cwd.glob(f'*_{sqid}_draft_chapter-two.md'))
        new_notes_files = list(cwd.glob(f'*_{sqid}_notes_chapter-two.md'))
        assert len(new_draft_files) == 1
        assert len(new_notes_files) == 1

        # Verify old files don't exist
        old_draft_files = list(cwd.glob(f'*_{sqid}_draft_chapter-one.md'))
        old_notes_files = list(cwd.glob(f'*_{sqid}_notes_chapter-one.md'))
        assert len(old_draft_files) == 0
        assert len(old_notes_files) == 0

        # Verify frontmatter updated
        draft_content = new_draft_files[0].read_text()
        frontmatter = yaml.safe_load(draft_content.split('---')[1])
        assert frontmatter['title'] == 'Chapter Two'


def test_rename_with_special_characters(tmp_path: Path) -> None:
    """Test renaming handles special characters correctly."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Rename with special characters
        result2 = runner.invoke(
            lmk,
            ['rename', f'@{sqid}', "Chapter 1: Hero's Journey!", '--directory', str(isolated_dir)],
        )
        assert result2.exit_code == 0

        # Verify files exist with slugified names
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*_{sqid}_draft_*.md'))
        assert len(draft_files) == 1
        assert 'hero' in draft_files[0].name.lower()


def test_rename_with_multiple_document_types(tmp_path: Path) -> None:
    """Test renaming updates all document types."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Add additional document types
        runner.invoke(lmk, ['types', 'add', 'characters', f'@{sqid}', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['types', 'add', 'worldbuilding', f'@{sqid}', '--directory', str(isolated_dir)])

        # Rename the node
        result2 = runner.invoke(lmk, ['rename', f'@{sqid}', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Verify all document types renamed
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*_{sqid}_draft_chapter-two.md'))
        notes_files = list(cwd.glob(f'*_{sqid}_notes_chapter-two.md'))
        char_files = list(cwd.glob(f'*_{sqid}_characters_chapter-two.md'))
        world_files = list(cwd.glob(f'*_{sqid}_worldbuilding_chapter-two.md'))

        assert len(draft_files) == 1
        assert len(notes_files) == 1
        assert len(char_files) == 1
        assert len(world_files) == 1

        # Verify old files don't exist
        old_files = list(cwd.glob(f'*_{sqid}_*_chapter-one.md'))
        assert len(old_files) == 0


def test_rename_preserves_sqid_and_path(tmp_path: Path) -> None:
    """Test renaming preserves SQID and materialized path."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child nodes
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk, ['add', 'Section 1.1', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)]
        )
        assert result2.exit_code == 0
        child_sqid = result2.output.split('@')[1].split(')')[0]

        # Get original MP for child
        cwd = Path.cwd()
        orig_draft = next(iter(cwd.glob(f'*_{child_sqid}_draft_*.md')))
        orig_mp = orig_draft.name.split('_')[0]

        # Rename child
        result3 = runner.invoke(lmk, ['rename', f'@{child_sqid}', 'Section 1.2', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # Verify SQID and MP preserved
        new_draft = next(iter(cwd.glob(f'*_{child_sqid}_draft_*.md')))
        new_mp = new_draft.name.split('_')[0]
        new_sqid = new_draft.name.split('_')[1]

        assert new_sqid == child_sqid
        assert new_mp == orig_mp


def test_rename_preserves_content(tmp_path: Path) -> None:
    """Test renaming preserves file content."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content to draft
        cwd = Path.cwd()
        draft_file = next(iter(cwd.glob(f'*_{sqid}_draft_*.md')))
        original_content = draft_file.read_text()
        additional_content = (
            '\n\nThis is important content that must be preserved.\n\n## Section 1\n\nMore content here.'
        )
        draft_file.write_text(original_content + additional_content)

        # Write content to notes
        notes_file = next(iter(cwd.glob(f'*_{sqid}_notes_*.md')))
        notes_file.write_text('Important notes here')

        # Rename the node
        result2 = runner.invoke(lmk, ['rename', f'@{sqid}', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Verify content preserved
        new_draft = next(iter(cwd.glob(f'*_{sqid}_draft_chapter-two.md')))
        new_draft_content = new_draft.read_text()
        assert 'This is important content that must be preserved.' in new_draft_content
        assert '## Section 1' in new_draft_content
        assert 'More content here.' in new_draft_content

        new_notes = next(iter(cwd.glob(f'*_{sqid}_notes_chapter-two.md')))
        new_notes_content = new_notes.read_text()
        assert new_notes_content == 'Important notes here'


def test_rename_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test renaming nonexistent node fails gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Try to rename nonexistent node
        result = runner.invoke(lmk, ['rename', '@NONEXISTENT', 'New Title', '--directory', str(isolated_dir)])
        assert result.exit_code != 0
        assert 'not found' in result.output


def test_rename_integration_with_list(tmp_path: Path) -> None:
    """Test renamed nodes appear correctly in list output."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid1 = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Rename first node
        result3 = runner.invoke(lmk, ['rename', f'@{sqid1}', 'Prologue', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0

        # List and verify new name appears
        result4 = runner.invoke(lmk, ['list', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert 'Prologue' in result4.output
        assert 'Chapter Two' in result4.output
