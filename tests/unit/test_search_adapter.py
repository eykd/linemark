"""Unit tests for SearchAdapter."""

from __future__ import annotations

import re
from pathlib import Path

from linemark.adapters.search_adapter import SearchAdapter


def test_search_adapter_filter_by_subtree_and_doctypes(tmp_path: Path) -> None:
    """Test filtering by both subtree and doctypes."""
    adapter = SearchAdapter()

    # Create test files
    (tmp_path / '100_ABC_draft_test.md').write_text('Draft content')
    (tmp_path / '100_ABC_notes_test.md').write_text('Notes content')
    (tmp_path / '100-100_DEF_draft_child.md').write_text('Child draft')
    (tmp_path / '100-100_DEF_notes_child.md').write_text('Child notes')
    (tmp_path / '200_GHI_draft_other.md').write_text('Other content')

    # Get files filtered by subtree "100" and doctypes ["draft", "notes"]
    files = list(adapter.get_files_in_outline_order(
        tmp_path,
        subtree_sqid='100',
        doctypes=['draft', 'notes']
    ))

    # Should include parent and child draft and notes files
    filenames = [f.name for f in files]
    assert '100_ABC_draft_test.md' in filenames
    assert '100_ABC_notes_test.md' in filenames
    assert '100-100_DEF_draft_child.md' in filenames
    assert '100-100_DEF_notes_child.md' in filenames
    assert '200_GHI_draft_other.md' not in filenames


def test_search_adapter_filter_by_doctypes_only(tmp_path: Path) -> None:
    """Test filtering by doctypes only."""
    adapter = SearchAdapter()

    # Create test files
    (tmp_path / '100_ABC_draft_test.md').write_text('Draft content')
    (tmp_path / '100_ABC_notes_test.md').write_text('Notes content')
    (tmp_path / '200_DEF_draft_other.md').write_text('Other draft')
    (tmp_path / '200_DEF_characters_other.md').write_text('Characters')

    # Get files filtered by doctypes only
    files = list(adapter.get_files_in_outline_order(
        tmp_path,
        doctypes=['draft', 'notes']
    ))

    filenames = [f.name for f in files]
    assert '100_ABC_draft_test.md' in filenames
    assert '100_ABC_notes_test.md' in filenames
    assert '200_DEF_draft_other.md' in filenames
    # Characters doctype should not be included
    assert '200_DEF_characters_other.md' not in filenames


def test_search_adapter_filter_by_subtree_only(tmp_path: Path) -> None:
    """Test filtering by subtree only."""
    adapter = SearchAdapter()

    # Create test files
    (tmp_path / '100_ABC_draft_test.md').write_text('Draft content')
    (tmp_path / '100_ABC_notes_test.md').write_text('Notes content')
    (tmp_path / '100-100_DEF_draft_child.md').write_text('Child draft')
    (tmp_path / '200_GHI_draft_other.md').write_text('Other content')

    # Get files filtered by subtree only
    files = list(adapter.get_files_in_outline_order(
        tmp_path,
        subtree_sqid='100'
    ))

    filenames = [f.name for f in files]
    assert '100_ABC_draft_test.md' in filenames
    assert '100_ABC_notes_test.md' in filenames
    assert '100-100_DEF_draft_child.md' in filenames
    assert '200_GHI_draft_other.md' not in filenames


def test_search_adapter_search_file(tmp_path: Path) -> None:
    """Test searching a single file."""
    adapter = SearchAdapter()

    # Create test file
    test_file = tmp_path / 'test.md'
    test_file.write_text('Line 1: Hello\nLine 2: World\nLine 3: Hello World')

    # Compile pattern
    pattern = re.compile(r'Hello')

    # Search file
    matches = list(adapter.search_file(test_file, pattern))

    assert len(matches) == 2
    assert matches[0] == (1, 'Line 1: Hello')
    assert matches[1] == (3, 'Line 3: Hello World')


def test_search_adapter_extract_sqid(tmp_path: Path) -> None:
    """Test extracting SQID from filename."""
    adapter = SearchAdapter()

    sqid = adapter.extract_sqid_from_filename('100_ABC123_draft_test.md')
    assert sqid == 'ABC123'

    sqid2 = adapter.extract_sqid_from_filename('100-200_XYZ789_notes_chapter.md')
    assert sqid2 == 'XYZ789'


def test_search_adapter_compile_pattern(tmp_path: Path) -> None:
    """Test pattern compilation with various flags."""
    adapter = SearchAdapter()

    # Case insensitive (default)
    pattern = adapter.compile_pattern('TEST')
    assert pattern.search('test') is not None
    assert pattern.search('TEST') is not None

    # Case sensitive
    pattern_cs = adapter.compile_pattern('TEST', case_sensitive=True)
    assert pattern_cs.search('test') is None
    assert pattern_cs.search('TEST') is not None

    # Literal
    pattern_lit = adapter.compile_pattern('[test]', literal=True)
    assert pattern_lit.search('[test]') is not None
    assert pattern_lit.search('t') is None  # Should not match character class

    # Multiline
    pattern_ml = adapter.compile_pattern('a.b', multiline=True)
    assert pattern_ml.search('a\nb') is not None


def test_search_adapter_search_outline(tmp_path: Path) -> None:
    """Test searching across outline files."""
    adapter = SearchAdapter()

    # Create test files
    (tmp_path / '100_ABC_draft_test.md').write_text('---\ntitle: Test\n---\nKeyword in draft')
    (tmp_path / '100_ABC_notes_test.md').write_text('---\ntitle: Test\n---\nKeyword in notes')
    (tmp_path / '200_DEF_draft_other.md').write_text('---\ntitle: Other\n---\nNo match here')

    # Compile pattern
    pattern = adapter.compile_pattern('Keyword')

    # Search outline
    results = list(adapter.search_outline(pattern, tmp_path))

    assert len(results) == 2
    assert all(r.sqid == 'ABC' for r in results)
    assert all('Keyword' in r.content for r in results)
    assert any('draft' in r.filename for r in results)
    assert any('notes' in r.filename for r in results)
