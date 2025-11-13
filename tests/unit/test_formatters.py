"""Unit tests for CLI formatters."""

from __future__ import annotations

from linemark.cli.formatters import format_json, format_tree
from linemark.domain.entities import SQID, MaterializedPath, Node, Outline


def test_format_tree_with_deep_hierarchy() -> None:
    """Test format_tree with multi-level hierarchy to cover all branches."""
    # Create outline with deep hierarchy
    outline = Outline()

    # Level 1 - root nodes
    root1 = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Root One',
        slug='root-one',
    )
    root2 = Node(
        sqid=SQID(value='def456'),
        mp=MaterializedPath(segments=(200,)),
        title='Root Two',
        slug='root-two',
    )

    # Level 2 - children of root1
    child1_1 = Node(
        sqid=SQID(value='ghi789'),
        mp=MaterializedPath(segments=(100, 100)),
        title='Child 1.1',
        slug='child-1-1',
    )
    child1_2 = Node(
        sqid=SQID(value='jkl012'),
        mp=MaterializedPath(segments=(100, 200)),
        title='Child 1.2',
        slug='child-1-2',
    )

    # Level 3 - grandchildren of root1
    grandchild1_1_1 = Node(
        sqid=SQID(value='mno345'),
        mp=MaterializedPath(segments=(100, 100, 100)),
        title='Grandchild 1.1.1',
        slug='grandchild-1-1-1',
    )
    grandchild1_2_1 = Node(
        sqid=SQID(value='pqr678'),
        mp=MaterializedPath(segments=(100, 200, 100)),
        title='Grandchild 1.2.1',
        slug='grandchild-1-2-1',
    )

    outline.add_node(root1)
    outline.add_node(root2)
    outline.add_node(child1_1)
    outline.add_node(child1_2)
    outline.add_node(grandchild1_1_1)
    outline.add_node(grandchild1_2_1)

    nodes = list(outline.nodes.values())
    nodes.sort(key=lambda n: n.mp.segments)

    result = format_tree(nodes)

    # Verify tree structure
    assert 'Root One' in result
    assert 'Root Two' in result
    assert 'Child 1.1' in result
    assert 'Child 1.2' in result
    assert 'Grandchild 1.1.1' in result
    assert 'Grandchild 1.2.1' in result

    # Verify tree connectors are present
    assert '├──' in result or '└──' in result

    # Verify that ancestor logic is exercised
    # The grandchildren should have proper indentation based on their ancestors
    lines = result.split('\n')

    # Find grandchild lines
    grandchild_1_1_1_line = next(line for line in lines if 'Grandchild 1.1.1' in line)
    grandchild_1_2_1_line = next(line for line in lines if 'Grandchild 1.2.1' in line)

    # Both should have indentation (spaces or pipes)
    assert '    ' in grandchild_1_1_1_line or '│   ' in grandchild_1_1_1_line
    assert '    ' in grandchild_1_2_1_line or '│   ' in grandchild_1_2_1_line


def test_format_tree_with_complex_ancestor_paths() -> None:
    """Test format_tree to ensure _build_prefix handles all ancestor scenarios.

    Creates a structure where we have:
    - Root (100)
      - Child A (100-100) - NOT last sibling
        - Grandchild A1 (100-100-100) - last sibling
      - Child B (100-200) - last sibling
        - Grandchild B1 (100-200-100) - last sibling
    """
    outline = Outline()

    root = Node(
        sqid=SQID(value='rootnode'),
        mp=MaterializedPath(segments=(100,)),
        title='Root',
        slug='root',
    )

    child_a = Node(
        sqid=SQID(value='childaaa'),
        mp=MaterializedPath(segments=(100, 100)),
        title='Child A',
        slug='child-a',
    )

    child_b = Node(
        sqid=SQID(value='childbbb'),
        mp=MaterializedPath(segments=(100, 200)),
        title='Child B',
        slug='child-b',
    )

    grandchild_a1 = Node(
        sqid=SQID(value='grandcha1'),
        mp=MaterializedPath(segments=(100, 100, 100)),
        title='Grandchild A1',
        slug='grandchild-a1',
    )

    grandchild_b1 = Node(
        sqid=SQID(value='grandchb1'),
        mp=MaterializedPath(segments=(100, 200, 100)),
        title='Grandchild B1',
        slug='grandchild-b1',
    )

    outline.add_node(root)
    outline.add_node(child_a)
    outline.add_node(child_b)
    outline.add_node(grandchild_a1)
    outline.add_node(grandchild_b1)

    nodes = list(outline.nodes.values())
    nodes.sort(key=lambda n: n.mp.segments)

    result = format_tree(nodes)

    # Verify structure is correct
    lines = result.split('\n')

    # Find the grandchild lines
    grandchild_a1_line = next(line for line in lines if 'Grandchild A1' in line)
    grandchild_b1_line = next(line for line in lines if 'Grandchild B1' in line)

    # Grandchild A1 should have '│   ' in its prefix because Child A is not the last sibling
    # This tests line 95 in formatters.py
    assert '│   ' in grandchild_a1_line

    # Grandchild B1 should have '    ' in its prefix because Child B is the last sibling
    # This tests line 93 in formatters.py
    assert '    ' in grandchild_b1_line


def test_format_json_empty_list() -> None:
    """Test format_json with empty node list."""
    result = format_json([])
    assert result == '[]'


def test_format_tree_empty_list() -> None:
    """Test format_tree with empty node list."""
    result = format_tree([])
    assert result == ''


# Doctype display tests (User Story 2)


def test_format_tree_with_show_doctypes() -> None:
    """Test format_tree displays doctypes when show_doctypes=True."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'draft', 'notes'},
    )

    result = format_tree([node], show_doctypes=True)

    assert 'Chapter One (@abc123)' in result
    assert 'doctypes: draft, notes' in result


def test_format_tree_with_show_doctypes_omits_empty() -> None:
    """Test format_tree omits doctype line when node has no doctypes."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types=set(),
    )

    result = format_tree([node], show_doctypes=True)

    assert 'Chapter One (@abc123)' in result
    assert 'doctypes:' not in result


def test_format_tree_with_multiple_doctypes() -> None:
    """Test format_tree displays multiple doctypes comma-separated and sorted."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'notes', 'draft', 'outline'},
    )

    result = format_tree([node], show_doctypes=True)

    # Should be alphabetically sorted
    assert 'doctypes: draft, notes, outline' in result


def test_format_json_with_show_doctypes() -> None:
    """Test format_json includes doctypes field when show_doctypes=True."""
    import json

    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'draft', 'notes'},
    )

    result = format_json([node], show_doctypes=True)
    data = json.loads(result)

    assert len(data) == 1
    assert 'doctypes' in data[0]
    assert sorted(data[0]['doctypes']) == ['draft', 'notes']


def test_format_json_with_show_doctypes_omits_when_empty() -> None:
    """Test format_json omits doctypes field when node has no doctypes."""
    import json

    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types=set(),
    )

    result = format_json([node], show_doctypes=True)
    data = json.loads(result)

    assert len(data) == 1
    assert 'doctypes' not in data[0]


def test_format_tree_without_show_doctypes_flag() -> None:
    """Test backward compatibility: format_tree without show_doctypes flag."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'draft', 'notes'},
    )

    # Without flag (default)
    result = format_tree([node])

    assert 'Chapter One (@abc123)' in result
    assert 'doctypes:' not in result


# File display tests (User Story 3)


def test_format_tree_with_show_files() -> None:
    """Test format_tree displays file paths when show_files=True."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'draft', 'notes'},
    )

    result = format_tree([node], show_files=True)

    assert 'Chapter One (@abc123)' in result
    assert 'files:' in result
    # Files should be shown in alphabetical order by doctype
    assert '100_abc123_draft_chapter-one.md' in result
    assert '100_abc123_notes_chapter-one.md' in result


def test_format_tree_with_show_files_omits_empty() -> None:
    """Test format_tree omits file line when node has no doctypes."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types=set(),
    )

    result = format_tree([node], show_files=True)

    assert 'Chapter One (@abc123)' in result
    assert 'files:' not in result


def test_format_tree_with_multiple_files() -> None:
    """Test format_tree displays all file paths for multiple doctypes."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'notes', 'draft', 'outline'},
    )

    result = format_tree([node], show_files=True)

    # All three files should be present, sorted alphabetically by doctype
    assert '100_abc123_draft_chapter-one.md' in result
    assert '100_abc123_notes_chapter-one.md' in result
    assert '100_abc123_outline_chapter-one.md' in result


def test_format_tree_with_long_file_paths() -> None:
    """Test format_tree displays full path for deeply nested nodes."""
    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100, 200, 300)),
        title='Deep Subsection',
        slug='deep-subsection',
        document_types={'draft'},
    )

    result = format_tree([node], show_files=True)

    # Should show the complete filename with full materialized path
    assert '100-200-300_abc123_draft_deep-subsection.md' in result


def test_format_json_with_show_files() -> None:
    """Test format_json includes files field when show_files=True."""
    import json

    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types={'draft', 'notes'},
    )

    result = format_json([node], show_files=True)
    data = json.loads(result)

    assert len(data) == 1
    assert 'files' in data[0]
    assert sorted(data[0]['files']) == [
        '100_abc123_draft_chapter-one.md',
        '100_abc123_notes_chapter-one.md',
    ]


def test_format_json_with_show_files_omits_when_empty() -> None:
    """Test format_json omits files field when node has no doctypes."""
    import json

    node = Node(
        sqid=SQID(value='abc123'),
        mp=MaterializedPath(segments=(100,)),
        title='Chapter One',
        slug='chapter-one',
        document_types=set(),
    )

    result = format_json([node], show_files=True)
    data = json.loads(result)

    assert len(data) == 1
    assert 'files' not in data[0]
