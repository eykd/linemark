"""Integration tests for outline compaction workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_compact_root_level_with_irregular_spacing(tmp_path: Path) -> None:
    """Test compacting root-level nodes with gaps."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create 4 nodes with irregular spacing: 001, 003, 007, 099
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node One',
        ])
        assert exit_code1 == 0

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node Two',
        ])
        assert exit_code2 == 0

        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node Three',
        ])
        assert exit_code3 == 0

        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node Four',
        ])
        assert exit_code4 == 0

        # Compact root level
        exit_code5, stdout5, _stderr5 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'compact'])
        assert exit_code5 == 0
        assert 'Compacted 4 root-level nodes' in stdout5

        # Verify new spacing uses 100s tier
        cwd = Path.cwd()
        files = list(cwd.glob('*.md'))
        file_names = [f.name for f in files]

        # Should have files starting with 100, 200, 300, 400
        assert any('100_' in name for name in file_names)
        assert any('200_' in name for name in file_names)
        assert any('300_' in name for name in file_names)
        assert any('400_' in name for name in file_names)

        # Verify old spacing gone
        assert not any('001_' in name for name in file_names)
        assert not any('002_' in name for name in file_names)


def test_compact_specific_subtree(tmp_path: Path) -> None:
    """Test compacting children of a specific node."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        # Add 3 children
        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child One',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0

        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child Two',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code3 == 0

        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child Three',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code4 == 0

        # Compact children of parent
        exit_code5, stdout5, _stderr5 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compact',
            f'@{parent_sqid}',
        ])
        assert exit_code5 == 0
        assert f'Compacted 3 children of @{parent_sqid}' in stdout5

        # Verify children now use even spacing (100, 200, 300)
        cwd = Path.cwd()
        children_files = list(cwd.glob('*-*_*.md'))
        file_names = [f.name for f in children_files]

        # Should have files with -100, -200, -300 in MP
        assert any('-100_' in name for name in file_names)
        assert any('-200_' in name for name in file_names)
        assert any('-300_' in name for name in file_names)


def test_compact_preserves_hierarchy(tmp_path: Path) -> None:
    """Test that compacting preserves parent-child relationships."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent with children
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Child',
            '--child-of',
            f'@{parent_sqid}',
        ])
        assert exit_code2 == 0

        # Add another root node
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Root Two',
        ])
        assert exit_code3 == 0

        # Compact root level
        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'compact'])
        assert exit_code4 == 0

        # Verify hierarchy intact via list
        _exit_code5, stdout5, _stderr5 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'list'])
        assert 'Parent' in stdout5
        assert 'Child' in stdout5
        assert 'Root Two' in stdout5


def test_compact_with_many_siblings_uses_smaller_tier(tmp_path: Path) -> None:
    """Test that compact uses appropriate tier based on sibling count."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create 12 root nodes to trigger 10s tier
        for i in range(1, 13):
            exit_code, _stdout, _stderr = invoke_asyncclick_command([
                'lmk',
                '--directory',
                str(isolated_dir),
                'add',
                f'Node {i}',
            ])
            assert exit_code == 0

        # Compact root level
        exit_code_compact, stdout_compact, _stderr_compact = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compact',
        ])
        assert exit_code_compact == 0
        assert 'Compacted 12 root-level nodes' in stdout_compact

        # Verify uses 10s tier: 010, 020, 030, ..., 120
        cwd = Path.cwd()
        files = list(cwd.glob('*.md'))
        file_names = [f.name for f in files]

        assert any('010_' in name for name in file_names)
        assert any('020_' in name for name in file_names)
        assert any('120_' in name for name in file_names)


def test_compact_preserves_content(tmp_path: Path) -> None:
    """Test that compacting preserves file contents."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create nodes
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid1 = stdout1.split('@')[1].split(')')[0]

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0

        # Write content to first chapter
        cwd = Path.cwd()
        draft_files = list(cwd.glob(f'*{sqid1}_draft*.md'))
        assert len(draft_files) == 1
        draft_file = draft_files[0]

        # Read original content
        original_content = draft_file.read_text()
        assert 'Chapter One' in original_content

        # Compact
        exit_code3, _stdout3, _stderr3 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'compact'])
        assert exit_code3 == 0

        # Find renamed file and verify content
        new_draft_files = list(cwd.glob(f'*{sqid1}_draft*.md'))
        assert len(new_draft_files) == 1
        new_draft_file = new_draft_files[0]

        new_content = new_draft_file.read_text()
        assert 'Chapter One' in new_content


def test_compact_nonexistent_node_fails(tmp_path: Path) -> None:
    """Test compacting nonexistent node fails gracefully."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        exit_code, stdout, stderr = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'compact',
            '@NONEXISTENT',
        ])
        assert exit_code != 0
        assert 'not found' in stdout or 'not found' in stderr


def test_compact_with_deep_hierarchy(tmp_path: Path) -> None:
    """Test compacting updates descendant paths correctly."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create parent
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Parent',
        ])
        assert exit_code1 == 0
        parent_sqid = stdout1.split('@')[1].split(')')[0]

        # Add child
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

        # Add grandchild
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Grandchild',
            '--child-of',
            f'@{child_sqid}',
        ])
        assert exit_code3 == 0
        grandchild_sqid = stdout3.split('@')[1].split(')')[0]

        # Add another root to trigger compaction
        exit_code4, _stdout4, _stderr4 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Root Two',
        ])
        assert exit_code4 == 0

        # Compact root level
        exit_code5, _stdout5, _stderr5 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'compact'])
        assert exit_code5 == 0

        # Verify grandchild file updated with new path prefix
        cwd = Path.cwd()
        grandchild_files = list(cwd.glob(f'*{grandchild_sqid}*.md'))
        assert len(grandchild_files) == 2  # draft + notes

        # Check that grandchild files have 3-segment MP (depth 3)
        grandchild_file = grandchild_files[0].name
        mp_part = grandchild_file.split('_')[0]
        assert mp_part.count('-') == 2  # 3-segment path has 2 dashes
