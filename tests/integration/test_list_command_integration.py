"""Integration tests for lmk list command."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def test_outline(tmp_path: Path) -> Path:
    """Create a test outline with hierarchical nodes."""
    # Root node
    (tmp_path / '001_sqid1_draft_chapter-one.md').write_text("""---
title: Chapter One
---
""")
    (tmp_path / '001_sqid1_notes_chapter-one.md').write_text('')

    # Child node (will be subtree root in some tests)
    (tmp_path / '001-100_sqid2_draft_section-one.md').write_text("""---
title: Section One
---
""")
    (tmp_path / '001-100_sqid2_notes_section-one.md').write_text('')

    # Grandchild node
    (tmp_path / '001-100-100_sqid3_draft_subsection.md').write_text("""---
title: Subsection
---
""")
    (tmp_path / '001-100-100_sqid3_notes_subsection.md').write_text('')

    # Sibling to sqid2 (not in subtree)
    (tmp_path / '001-200_sqid4_draft_section-two.md').write_text("""---
title: Section Two
---
""")
    (tmp_path / '001-200_sqid4_notes_section-two.md').write_text('')

    # Another root node
    (tmp_path / '002_sqid5_draft_chapter-two.md').write_text("""---
title: Chapter Two
---
""")
    (tmp_path / '002_sqid5_notes_chapter-two.md').write_text('')

    return tmp_path


def test_list_command_with_sqid_filters_to_subtree(test_outline: Path) -> None:
    """Test lmk list @<sqid> filters to subtree."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command(['lmk', '--directory', str(test_outline), 'list', '@sqid2'])

    assert exit_code == 0
    output = stdout

    # Should contain subtree root and its descendant
    assert 'Section One (@sqid2)' in output
    assert 'Subsection (@sqid3)' in output

    # Should NOT contain nodes outside subtree
    assert 'Chapter One (@sqid1)' not in output  # Parent
    assert 'Section Two (@sqid4)' not in output  # Sibling
    assert 'Chapter Two (@sqid5)' not in output  # Other root


def test_list_command_with_invalid_sqid_shows_error(test_outline: Path) -> None:
    """Test lmk list @<invalid> shows error message."""
    CliRunner()
    exit_code, stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', str(test_outline), 'list', '@invalid'])

    assert exit_code == 1
    output = stdout + stderr
    assert 'Error: SQID invalid not found in outline' in output


def test_list_command_without_args_returns_full_outline(test_outline: Path) -> None:
    """Test backward compatibility: lmk list without args returns full outline."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command(['lmk', '--directory', str(test_outline), 'list'])

    assert exit_code == 0
    output = stdout

    # Should contain all nodes
    assert 'Chapter One (@sqid1)' in output
    assert 'Section One (@sqid2)' in output
    assert 'Subsection (@sqid3)' in output
    assert 'Section Two (@sqid4)' in output
    assert 'Chapter Two (@sqid5)' in output


# User Story 2: Show Doctypes tests


def test_list_command_with_show_doctypes(test_outline: Path) -> None:
    """Test lmk list --show-doctypes displays doctypes in tree output."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '--show-doctypes',
    ])

    assert exit_code == 0
    output = stdout

    # Should contain nodes
    assert 'Chapter One (@sqid1)' in output

    # Should contain doctype metadata
    assert 'doctypes: draft, notes' in output


def test_list_command_with_show_doctypes_json(test_outline: Path) -> None:
    """Test lmk list --show-doctypes --json includes doctypes field."""
    import json

    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '--show-doctypes',
        '--json',
    ])

    assert exit_code == 0
    data = json.loads(stdout)

    # Check that doctypes field is present
    root_node = data[0]
    assert 'doctypes' in root_node
    assert sorted(root_node['doctypes']) == ['draft', 'notes']


def test_list_command_with_sqid_and_show_doctypes(test_outline: Path) -> None:
    """Test combining SQID filtering with --show-doctypes."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '@sqid2',
        '--show-doctypes',
    ])

    assert exit_code == 0
    output = stdout

    # Should show subtree
    assert 'Section One (@sqid2)' in output
    assert 'Subsection (@sqid3)' in output

    # Should NOT show nodes outside subtree
    assert 'Chapter One (@sqid1)' not in output

    # Should show doctypes
    assert 'doctypes: draft, notes' in output


# User Story 3: Show Files tests


def test_list_command_with_show_files(test_outline: Path) -> None:
    """Test lmk list --show-files displays file paths in tree output."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '--show-files',
    ])

    assert exit_code == 0
    output = stdout

    # Should contain nodes
    assert 'Chapter One (@sqid1)' in output

    # Should contain file metadata
    assert 'files:' in output
    assert '001_sqid1_draft_chapter-one.md' in output
    assert '001_sqid1_notes_chapter-one.md' in output


def test_list_command_with_show_files_json(test_outline: Path) -> None:
    """Test lmk list --show-files --json includes files field."""
    import json

    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '--show-files',
        '--json',
    ])

    assert exit_code == 0
    data = json.loads(stdout)

    # Check that files field is present
    root_node = data[0]
    assert 'files' in root_node
    assert sorted(root_node['files']) == [
        '001_sqid1_draft_chapter-one.md',
        '001_sqid1_notes_chapter-one.md',
    ]


def test_list_command_with_sqid_and_show_files(test_outline: Path) -> None:
    """Test combining SQID filtering with --show-files."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '@sqid2',
        '--show-files',
    ])

    assert exit_code == 0
    output = stdout

    # Should show subtree
    assert 'Section One (@sqid2)' in output
    assert 'Subsection (@sqid3)' in output

    # Should NOT show nodes outside subtree
    assert 'Chapter One (@sqid1)' not in output

    # Should show files
    assert 'files:' in output
    assert '001-100_sqid2_draft_section-one.md' in output


# User Story 4: Combined Flags tests


def test_list_command_with_all_flags_tree(test_outline: Path) -> None:
    """Test lmk list with @SQID, --show-doctypes, and --show-files in tree output."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '@sqid2',
        '--show-doctypes',
        '--show-files',
    ])

    assert exit_code == 0
    output = stdout

    # Should show subtree nodes
    assert 'Section One (@sqid2)' in output
    assert 'Subsection (@sqid3)' in output

    # Should NOT show nodes outside subtree
    assert 'Chapter One (@sqid1)' not in output

    # Should show doctypes (metadata order: doctypes first)
    assert 'doctypes: draft, notes' in output

    # Should show files (after doctypes)
    assert 'files:' in output
    assert '001-100_sqid2_draft_section-one.md' in output


def test_list_command_with_all_flags_json(test_outline: Path) -> None:
    """Test lmk list with @SQID, --show-doctypes, --show-files, and --json."""
    import json

    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '@sqid2',
        '--show-doctypes',
        '--show-files',
        '--json',
    ])

    assert exit_code == 0
    data = json.loads(stdout)

    # Should contain subtree root
    assert len(data) == 1
    root_node = data[0]
    assert root_node['sqid'] == 'sqid2'

    # Should have both doctypes and files fields
    assert 'doctypes' in root_node
    assert sorted(root_node['doctypes']) == ['draft', 'notes']
    assert 'files' in root_node
    assert sorted(root_node['files']) == [
        '001-100_sqid2_draft_section-one.md',
        '001-100_sqid2_notes_section-one.md',
    ]


def test_list_command_metadata_order_tree(test_outline: Path) -> None:
    """Test that metadata appears in correct order: doctypes first, then files."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command([
        'lmk',
        '--directory',
        str(test_outline),
        'list',
        '--show-doctypes',
        '--show-files',
    ])

    assert exit_code == 0
    output = stdout

    # Find position of doctypes and files metadata
    doctypes_pos = output.find('doctypes:')
    files_pos = output.find('files:')

    # Both should be present
    assert doctypes_pos != -1
    assert files_pos != -1

    # Doctypes should appear before files
    assert doctypes_pos < files_pos


def test_list_command_backward_compat_no_flags(test_outline: Path) -> None:
    """Test backward compatibility: lmk list without any flags."""
    CliRunner()
    exit_code, stdout, _stderr = invoke_asyncclick_command(['lmk', '--directory', str(test_outline), 'list'])

    assert exit_code == 0
    output = stdout

    # Should show all nodes
    assert 'Chapter One (@sqid1)' in output
    assert 'Section One (@sqid2)' in output

    # Should NOT show metadata
    assert 'doctypes:' not in output
    assert 'files:' not in output
