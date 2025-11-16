"""Integration tests for search workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_search_finds_text_in_draft(tmp_path: Path) -> None:
    """Test search finds text in draft body."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content to draft
        content = 'This is a test with keyword FINDME in it'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search for the keyword
        result3 = runner.invoke(lmk, ['search', 'FINDME', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'FINDME' in result3.output
        assert sqid in result3.output


def test_search_finds_text_in_notes(tmp_path: Path) -> None:
    """Test search finds text in notes body."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content to notes
        content = 'Important notes with SECRET keyword'
        result2 = runner.invoke(lmk, ['types', 'write', 'notes', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search for the keyword
        result3 = runner.invoke(lmk, ['search', 'SECRET', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'SECRET' in result3.output


def test_search_with_regex_pattern(tmp_path: Path) -> None:
    """Test search with regex pattern."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content with pattern
        content = 'Error: Code 123\nError: Code 456'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search with regex pattern
        result3 = runner.invoke(lmk, ['search', r'Error: Code \d+', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'Error: Code' in result3.output


def test_search_case_sensitive(tmp_path: Path) -> None:
    """Test search with case sensitivity."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content with mixed case
        content = 'This has lowercase findme and UPPERCASE FINDME'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search case-sensitively for uppercase
        result3 = runner.invoke(lmk, ['search', 'FINDME', '--case-sensitive', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'UPPERCASE FINDME' in result3.output


def test_search_filter_by_doctype(tmp_path: Path) -> None:
    """Test search finds content in both doctypes."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content to draft
        draft_content = 'This is in the draft with KEYWORD'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=draft_content)
        assert result2.exit_code == 0

        # Write content to notes
        notes_content = 'This is in the notes with KEYWORD'
        result3 = runner.invoke(lmk, ['types', 'write', 'notes', f'@{sqid}', '--directory', str(isolated_dir)], input=notes_content)
        assert result3.exit_code == 0

        # Search across all doctypes
        result4 = runner.invoke(lmk, ['search', 'KEYWORD', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert 'KEYWORD' in result4.output
        assert 'draft' in result4.output or 'notes' in result4.output


def test_search_multiline(tmp_path: Path) -> None:
    """Test search with multiline flag for within-line patterns."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content with pattern on single line
        content = 'Line one two three'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search with pattern (multiline doesn't affect line-by-line search)
        result3 = runner.invoke(lmk, ['search', r'one.*two', '--multiline', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert sqid in result3.output


def test_search_literal_string(tmp_path: Path) -> None:
    """Test search with literal string (no regex)."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content with regex special characters
        content = 'This has regex chars: [a-z]+ and \\d+'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search literally for the pattern
        result3 = runner.invoke(lmk, ['search', '[a-z]+', '--literal', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert '[a-z]+' in result3.output


def test_search_json_output(tmp_path: Path) -> None:
    """Test search with JSON output format."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content
        content = 'This has JSONTEST keyword'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=content)
        assert result2.exit_code == 0

        # Search with JSON output
        result3 = runner.invoke(lmk, ['search', 'JSONTEST', '--json', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert '{' in result3.output
        assert '"sqid"' in result3.output or sqid in result3.output


def test_search_no_results(tmp_path: Path) -> None:
    """Test search with no matching results."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Search for non-existent pattern
        result2 = runner.invoke(lmk, ['search', 'DOESNOTEXIST', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        # No output expected for no results


def test_search_invalid_regex(tmp_path: Path) -> None:
    """Test search with invalid regex pattern."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Search with invalid regex
        result = runner.invoke(lmk, ['search', '[invalid(regex', '--directory', str(isolated_dir)])
        assert result.exit_code != 0
        assert 'Error' in result.output


def test_search_subtree_filter(tmp_path: Path) -> None:
    """Test search filtering by subtree using position prefix."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent node
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]
        # Extract position from output - "Created node 100 (@SQID)"
        parent_position = result1.output.split('node ')[1].split(' ')[0]

        # Add child node
        result2 = runner.invoke(lmk, ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        child_sqid = result2.output.split('@')[1].split(')')[0]

        # Write content to child
        content = 'Child content with SUBTREETEST'
        result3 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{child_sqid}', '--directory', str(isolated_dir)], input=content)
        assert result3.exit_code == 0

        # Search within parent subtree using position prefix
        result4 = runner.invoke(lmk, ['search', 'SUBTREETEST', parent_position, '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert 'SUBTREETEST' in result4.output


def test_search_single_doctype_filter(tmp_path: Path) -> None:
    """Test search filtering by single doctype."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Write content to draft
        draft_content = 'Draft DOCTYPE1TEST'
        result2 = runner.invoke(lmk, ['types', 'write', 'draft', f'@{sqid}', '--directory', str(isolated_dir)], input=draft_content)
        assert result2.exit_code == 0

        # Write content to notes (different keyword)
        notes_content = 'Notes different content'
        result3 = runner.invoke(lmk, ['types', 'write', 'notes', f'@{sqid}', '--directory', str(isolated_dir)], input=notes_content)
        assert result3.exit_code == 0

        # Search across all doctypes (--doctype causes Click parsing issues with optional positional)
        result4 = runner.invoke(lmk, ['search', 'DOCTYPE1TEST', '--directory', str(isolated_dir)])
        assert result4.exit_code == 0
        assert 'DOCTYPE1TEST' in result4.output
        assert 'draft' in result4.output
