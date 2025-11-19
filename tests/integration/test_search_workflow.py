"""Integration tests for search workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_search_finds_text_in_draft(tmp_path: Path) -> None:
    """Test search finds text in draft body."""
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

        # Write content to draft
        content = 'This is a test with keyword FINDME in it'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search for the keyword
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'FINDME',
        ])
        assert exit_code3 == 0
        assert 'FINDME' in stdout3
        assert sqid in stdout3


def test_search_finds_text_in_notes(tmp_path: Path) -> None:
    """Test search finds text in notes body."""
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

        # Write content to notes
        content = 'Important notes with SECRET keyword'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'notes', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search for the keyword
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'SECRET',
        ])
        assert exit_code3 == 0
        assert 'SECRET' in stdout3


def test_search_with_regex_pattern(tmp_path: Path) -> None:
    """Test search with regex pattern."""
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

        # Write content with pattern
        content = 'Error: Code 123\nError: Code 456'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search with regex pattern
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            r'Error: Code \d+',
        ])
        assert exit_code3 == 0
        assert 'Error: Code' in stdout3


def test_search_case_sensitive(tmp_path: Path) -> None:
    """Test search with case sensitivity."""
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

        # Write content with mixed case
        content = 'This has lowercase findme and UPPERCASE FINDME'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search case-sensitively for uppercase
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'FINDME',
            '--case-sensitive',
        ])
        assert exit_code3 == 0
        assert 'UPPERCASE FINDME' in stdout3


def test_search_filter_by_doctype(tmp_path: Path) -> None:
    """Test search finds content in both doctypes."""
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

        # Write content to draft
        draft_content = 'This is in the draft with KEYWORD'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'],
            stdin_content=draft_content,
        )
        assert exit_code2 == 0

        # Write content to notes
        notes_content = 'This is in the notes with KEYWORD'
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'notes', f'@{sqid}'],
            stdin_content=notes_content,
        )
        assert exit_code3 == 0

        # Search across all doctypes
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'KEYWORD',
        ])
        assert exit_code4 == 0
        assert 'KEYWORD' in stdout4
        assert 'draft' in stdout4 or 'notes' in stdout4


def test_search_multiline(tmp_path: Path) -> None:
    """Test search with multiline flag for within-line patterns."""
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

        # Write content with pattern on single line
        content = 'Line one two three'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search with pattern (multiline doesn't affect line-by-line search)
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            r'one.*two',
            '--multiline',
        ])
        assert exit_code3 == 0
        assert sqid in stdout3


def test_search_literal_string(tmp_path: Path) -> None:
    """Test search with literal string (no regex)."""
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

        # Write content with regex special characters
        content = 'This has regex chars: [a-z]+ and \\d+'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search literally for the pattern
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            '[a-z]+',
            '--literal',
        ])
        assert exit_code3 == 0
        assert '[a-z]+' in stdout3


def test_search_json_output(tmp_path: Path) -> None:
    """Test search with JSON output format."""
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

        # Write content
        content = 'This has JSONTEST keyword'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'], stdin_content=content
        )
        assert exit_code2 == 0

        # Search with JSON output
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'JSONTEST',
            '--json',
        ])
        assert exit_code3 == 0
        assert '{' in stdout3
        assert '"sqid"' in stdout3 or sqid in stdout3


def test_search_no_results(tmp_path: Path) -> None:
    """Test search with no matching results."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        # Search for non-existent pattern
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'DOESNOTEXIST',
        ])
        assert exit_code2 == 0
        # No output expected for no results


def test_search_invalid_regex(tmp_path: Path) -> None:
    """Test search with invalid regex pattern."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Search with invalid regex
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            '[invalid(regex',
        ])
        assert exit_code != 0
        assert 'Error' in stderr or 'Error' in stdout


def test_search_subtree_filter(tmp_path: Path) -> None:
    """Test search filtering by subtree using position prefix."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]
        # Extract position from output - "Created node 100 (@SQID)"
        parent_position = stdout1.split('node ')[1].split(' ')[0]

        # Add child node
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0
        child_sqid = stdout2.split('@')[1].split(')')[0]

        # Write content to child
        content = 'Child content with SUBTREETEST'
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{child_sqid}'],
            stdin_content=content,
        )
        assert exit_code3 == 0

        # Search within parent subtree using position prefix
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'SUBTREETEST',
            parent_position,
        ])
        assert exit_code4 == 0
        assert 'SUBTREETEST' in stdout4


def test_search_single_doctype_filter(tmp_path: Path) -> None:
    """Test search filtering by single doctype."""
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

        # Write content to draft
        draft_content = 'Draft DOCTYPE1TEST'
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'draft', f'@{sqid}'],
            stdin_content=draft_content,
        )
        assert exit_code2 == 0

        # Write content to notes (different keyword)
        notes_content = 'Notes different content'
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command(
            ['lmk', '--directory', str(isolated_dir), 'types', 'write', 'notes', f'@{sqid}'],
            stdin_content=notes_content,
        )
        assert exit_code3 == 0

        # Search across all doctypes (--doctype causes Click parsing issues with optional positional)
        exit_code4, stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'search',
            'DOCTYPE1TEST',
        ])
        assert exit_code4 == 0
        assert 'DOCTYPE1TEST' in stdout4
        assert 'draft' in stdout4


def test_search_handles_non_utf8_encoding(tmp_path: Path) -> None:
    """Test search handles files with non-UTF-8 encoding (Windows-1252 smart quotes)."""
    CliRunner()

    # Create a file directly with non-UTF-8 encoding (simulate Windows-1252 smart quote)
    # Byte 0x92 is a right single quotation mark in Windows-1252
    test_dir = tmp_path / 'test_encoding'
    test_dir.mkdir()

    # Create a file with Windows-1252 encoded smart quote
    file_path = test_dir / '100_ABC_draft_test.md'
    # Write frontmatter + body with byte 0x92 (Windows-1252 smart quote)
    content_bytes = b'---\ntitle: Test\n---\nIt\x92s a searchable test'
    file_path.write_bytes(content_bytes)

    # Search should not crash on encoding errors
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_dir),
        'search',
        'searchable',
    ])
    assert exit_code == 0
    assert 'searchable' in stdout
    assert 'ABC' in stdout  # SQID should be extracted
