"""Integration tests for compile doctype workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


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
        _exit_code_add1, _stdout_add1, _stderr_add1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Extract SQID from first node to add a child
        _exit_code_list, stdout_list, _stderr_list = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        import json

        nodes_tree = json.loads(stdout_list)
        nodes = flatten_nodes(nodes_tree)
        first_sqid = nodes[0]['sqid']

        _exit_code_add2, _stdout_add2, _stderr_add2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            first_sqid,
        ])
        _exit_code_add3, _stdout_add3, _stderr_add3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])

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
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
        ])

        assert exit_code == 0
        assert 'Chapter One content' in stdout
        assert 'Section 1.1 content' in stdout
        assert 'Chapter Two content' in stdout
        # Should be in depth-first order: Chapter One, Section 1.1, Chapter Two
        assert stdout.index('Chapter One content') < stdout.index('Section 1.1 content')
        assert stdout.index('Section 1.1 content') < stdout.index('Chapter Two content')


def test_compile_skips_empty_files(tmp_path: Path) -> None:
    """Test T023: Skip empty files during compilation."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add three nodes
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        _exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        _exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Three',
        ])

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
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
        ])

        assert exit_code == 0
        assert 'First chapter content' in stdout
        assert 'Third chapter content' in stdout
        # Should only have one separator (between the two non-empty files)
        assert stdout.count('\n\n---\n\n') == 1


def test_compile_doctype_not_found_error(tmp_path: Path) -> None:
    """Test T024: Error when doctype doesn't exist."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node (only has draft and notes by default)
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Try to compile a non-existent doctype
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'summary',
        ])

        assert exit_code == 1
        output = stdout + stderr
        assert 'Error:' in output
        assert 'summary' in output
        assert 'not found' in output.lower()


def test_compile_empty_result_handling(tmp_path: Path) -> None:
    """Test T025: Empty result when all files are empty."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes but don't add any content
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        _exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])

        # Compile (all draft files have only frontmatter, no actual content)
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
        ])

        # Should succeed with empty output
        assert exit_code == 0
        assert stdout.strip() == ''


# =============================================================================
# User Story 2: Subtree Support Integration Tests (T036-T040)
# =============================================================================


def test_subtree_compilation_with_children(tmp_path: Path) -> None:
    """Test T036: Compile subtree with children."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and children
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        # Extract SQID
        _exit_code_list, stdout_list, _stderr_list = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        import json

        nodes = flatten_nodes(json.loads(stdout_list))
        chapter_one_sqid = nodes[0]['sqid']

        # Add child and grandchild
        _exit_code_add2, _stdout_add2, _stderr_add2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            chapter_one_sqid,
        ])
        _exit_code_list2, stdout_list2, _stderr_list2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        nodes2 = flatten_nodes(json.loads(stdout_list2))
        # Find Section 1.1 by title
        section_sqid = next(n['sqid'] for n in nodes2 if n['title'] == 'Section 1.1')

        _exit_code_add3, _stdout_add3, _stderr_add3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Subsection 1.1.1',
            '--child-of',
            section_sqid,
        ])

        # Add another root node
        _exit_code_add4, _stdout_add4, _stderr_add4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])

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
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
            section_sqid,
        ])

        assert exit_code == 0
        assert 'Section 1.1 content' in stdout
        assert 'Subsection content' in stdout
        # Should NOT include parent or other branches
        assert 'Chapter One content' not in stdout
        assert 'Chapter Two content' not in stdout


def test_leaf_node_subtree_compilation(tmp_path: Path) -> None:
    """Test T037: Compile subtree for leaf node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add multiple nodes
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        _exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])

        # Get SQID of Chapter Two
        _exit_code_list, stdout_list, _stderr_list = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        import json

        nodes = flatten_nodes(json.loads(stdout_list))
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
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
            chapter_two_sqid,
        ])

        assert exit_code == 0
        assert 'Chapter Two content' in stdout
        assert 'Chapter One content' not in stdout


def test_invalid_sqid_error_integration(tmp_path: Path) -> None:
    """Test T038: Error for invalid SQID."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add a node
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Try to compile with invalid SQID
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
            'INVALID123',
        ])

        assert exit_code == 1
        output = stdout + stderr
        assert 'Error:' in output
        assert 'INVALID123' in output


def test_subtree_with_no_matching_doctype_integration(tmp_path: Path) -> None:
    """Test T039: Error when subtree has no matching doctype."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add parent and child
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Get SQID
        _exit_code_list, stdout_list, _stderr_list = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        import json

        nodes = flatten_nodes(json.loads(stdout_list))
        sqid = nodes[0]['sqid']

        _exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Section 1.1',
            '--child-of',
            sqid,
        ])

        # Try to compile non-existent doctype from subtree
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'summary',
            sqid,
        ])

        assert exit_code == 1
        output = stdout + stderr
        assert 'Error:' in output
        assert 'summary' in output
        assert 'not found' in output.lower()


def test_at_prefix_stripping_integration(tmp_path: Path) -> None:
    """Test T040: @ prefix is stripped from SQID."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Add nodes
        _exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])

        # Get SQID
        _exit_code_list, stdout_list, _stderr_list = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'list',
            '--json',
        ])
        import json

        nodes = flatten_nodes(json.loads(stdout_list))
        sqid = nodes[0]['sqid']

        # Add content
        cwd = Path.cwd()
        for draft_file in cwd.glob('*_draft_*.md'):
            content = draft_file.read_text()
            draft_file.write_text(content + '\n\nChapter content')

        # Compile with @ prefix
        exit_code, stdout, _stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compile',
            'draft',
            f'@{sqid}',
        ])

        assert exit_code == 0
        assert 'Chapter content' in stdout
