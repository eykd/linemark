"""Integration tests for compile doctype workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from click.testing import CliRunner

from linemark.cli.main import lmk


def flatten_nodes(nodes: list[Any]) -> list[dict[str, Any]]:
    """Flatten tree-structured JSON nodes to a flat list."""
    result: list[dict[str, Any]] = []
    for node in nodes:
        # Add the node itself (without children key)
        node_copy = {k: v for k, v in node.items() if k != 'children'}
        result.append(node_copy)
        # Recursively add children
        if node.get('children'):
            result.extend(flatten_nodes(node['children']))
    return result


def test_compile_multiple_nodes(tmp_path: Path) -> None:
    """Test T022: Compile multiple nodes in hierarchical order."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add several nodes
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Extract SQID from first node to add a child
        result_list = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        import json

        nodes_tree = json.loads(result_list.output)
        nodes = flatten_nodes(nodes_tree)
        first_sqid = nodes[0]['sqid']

        runner.invoke(lmk, ['add', 'Section 1.1', '--child-of', first_sqid, '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])

        # Add content to draft files by title
        cwd = Path.cwd()
        draft_files = list(cwd.glob('*_draft_*.md'))

        # Modify draft files to add content based on their title
        for draft_file in draft_files:
            content = draft_file.read_text()
            if 'Chapter One' in content:
                draft_file.write_text(content + '\n\nChapter One content')
            elif 'Section 1.1' in content:
                draft_file.write_text(content + '\n\nSection 1.1 content')
            elif 'Chapter Two' in content:
                draft_file.write_text(content + '\n\nChapter Two content')

        # Compile all drafts
        result = runner.invoke(lmk, ['compile', 'draft', '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'Chapter One content' in result.output
        assert 'Section 1.1 content' in result.output
        assert 'Chapter Two content' in result.output
        # Should be in depth-first order: Chapter One, Section 1.1, Chapter Two
        assert result.output.index('Chapter One content') < result.output.index('Section 1.1 content')
        assert result.output.index('Section 1.1 content') < result.output.index('Chapter Two content')


def test_compile_skips_empty_files(tmp_path: Path) -> None:
    """Test T023: Skip empty files during compilation."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add three nodes
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Three', '--directory', str(isolated_dir)])

        # Add content only to first and third nodes
        cwd = Path.cwd()
        draft_files = sorted(cwd.glob('*_draft_*.md'))

        # Add content to first file
        content1 = draft_files[0].read_text()
        draft_files[0].write_text(content1 + '\n\nFirst chapter content')

        # Leave second file empty (just frontmatter)

        # Add content to third file
        content3 = draft_files[2].read_text()
        draft_files[2].write_text(content3 + '\n\nThird chapter content')

        # Compile
        result = runner.invoke(lmk, ['compile', 'draft', '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'First chapter content' in result.output
        assert 'Third chapter content' in result.output
        # Should only have one separator (between the two non-empty files)
        assert result.output.count('\n\n---\n\n') == 1


def test_compile_doctype_not_found_error(tmp_path: Path) -> None:
    """Test T024: Error when doctype doesn't exist."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node (only has draft and notes by default)
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Try to compile a non-existent doctype
        result = runner.invoke(lmk, ['compile', 'summary', '--directory', str(isolated_dir)])

        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'summary' in result.output
        assert 'not found' in result.output.lower()


def test_compile_empty_result_handling(tmp_path: Path) -> None:
    """Test T025: Empty result when all files are empty."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes but don't add any content
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])

        # Compile (all draft files have only frontmatter, no actual content)
        result = runner.invoke(lmk, ['compile', 'draft', '--directory', str(isolated_dir)])

        # Should succeed with empty output
        assert result.exit_code == 0
        assert result.output.strip() == ''


# =============================================================================
# User Story 2: Subtree Support Integration Tests (T036-T040)
# =============================================================================


def test_subtree_compilation_with_children(tmp_path: Path) -> None:
    """Test T036: Compile subtree with children."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and children
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        # Extract SQID
        result_list = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        import json

        nodes = flatten_nodes(json.loads(result_list.output))
        chapter_one_sqid = nodes[0]['sqid']

        # Add child and grandchild
        runner.invoke(lmk, ['add', 'Section 1.1', '--child-of', chapter_one_sqid, '--directory', str(isolated_dir)])
        result_list2 = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        nodes2 = flatten_nodes(json.loads(result_list2.output))
        # Find Section 1.1 by title
        section_sqid = next(n['sqid'] for n in nodes2 if n['title'] == 'Section 1.1')

        runner.invoke(lmk, ['add', 'Subsection 1.1.1', '--child-of', section_sqid, '--directory', str(isolated_dir)])

        # Add another root node
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])

        # Add content to files
        cwd = Path.cwd()
        for draft_file in cwd.glob('*_draft_*.md'):
            content = draft_file.read_text()
            if 'Chapter One' in content:
                draft_file.write_text(content + '\n\nChapter One content')
            elif 'Section 1.1' in content:
                draft_file.write_text(content + '\n\nSection 1.1 content')
            elif 'Subsection 1.1.1' in content:
                draft_file.write_text(content + '\n\nSubsection content')
            elif 'Chapter Two' in content:
                draft_file.write_text(content + '\n\nChapter Two content')

        # Compile only Section 1.1 subtree
        result = runner.invoke(lmk, ['compile', 'draft', section_sqid, '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'Section 1.1 content' in result.output
        assert 'Subsection content' in result.output
        # Should NOT include parent or other branches
        assert 'Chapter One content' not in result.output
        assert 'Chapter Two content' not in result.output


def test_leaf_node_subtree_compilation(tmp_path: Path) -> None:
    """Test T037: Compile subtree for leaf node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add multiple nodes
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])

        # Get SQID of Chapter Two
        result_list = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        import json

        nodes = flatten_nodes(json.loads(result_list.output))
        chapter_two_sqid = next(n['sqid'] for n in nodes if n['title'] == 'Chapter Two')

        # Add content
        cwd = Path.cwd()
        for draft_file in cwd.glob('*_draft_*.md'):
            content = draft_file.read_text()
            if 'Chapter One' in content:
                draft_file.write_text(content + '\n\nChapter One content')
            elif 'Chapter Two' in content:
                draft_file.write_text(content + '\n\nChapter Two content')

        # Compile leaf node subtree
        result = runner.invoke(lmk, ['compile', 'draft', chapter_two_sqid, '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'Chapter Two content' in result.output
        assert 'Chapter One content' not in result.output


def test_invalid_sqid_error_integration(tmp_path: Path) -> None:
    """Test T038: Error for invalid SQID."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Try to compile with invalid SQID
        result = runner.invoke(lmk, ['compile', 'draft', 'INVALID123', '--directory', str(isolated_dir)])

        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'INVALID123' in result.output


def test_subtree_with_no_matching_doctype_integration(tmp_path: Path) -> None:
    """Test T039: Error when subtree has no matching doctype."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Get SQID
        result_list = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        import json

        nodes = flatten_nodes(json.loads(result_list.output))
        sqid = nodes[0]['sqid']

        runner.invoke(lmk, ['add', 'Section 1.1', '--child-of', sqid, '--directory', str(isolated_dir)])

        # Try to compile non-existent doctype from subtree
        result = runner.invoke(lmk, ['compile', 'summary', sqid, '--directory', str(isolated_dir)])

        assert result.exit_code == 1
        assert 'Error:' in result.output
        assert 'summary' in result.output
        assert 'not found' in result.output.lower()


def test_at_prefix_stripping_integration(tmp_path: Path) -> None:
    """Test T040: @ prefix is stripped from SQID."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes
        runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])

        # Get SQID
        result_list = runner.invoke(lmk, ['list', '--json', '--directory', str(isolated_dir)])
        import json

        nodes = flatten_nodes(json.loads(result_list.output))
        sqid = nodes[0]['sqid']

        # Add content
        cwd = Path.cwd()
        for draft_file in cwd.glob('*_draft_*.md'):
            content = draft_file.read_text()
            draft_file.write_text(content + '\n\nChapter content')

        # Compile with @ prefix
        result = runner.invoke(lmk, ['compile', 'draft', f'@{sqid}', '--directory', str(isolated_dir)])

        assert result.exit_code == 0
        assert 'Chapter content' in result.output
