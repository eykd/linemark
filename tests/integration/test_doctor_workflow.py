"""Integration tests for doctor (validate/repair) workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from tests.conftest import invoke_asyncclick_command


def test_doctor_validates_clean_outline(tmp_path: Path) -> None:
    """Test doctor command on valid outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create valid outline
        exit_code1, _stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0

        exit_code2, _stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0

        # Run doctor
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code3 == 0
        assert 'valid' in stdout3.lower()


def test_doctor_detects_missing_notes_file(tmp_path: Path) -> None:
    """Test doctor detects missing required files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Delete notes file to create invalid state
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files) == 1
        notes_files[0].unlink()

        # Run doctor (should detect issue)
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code2 != 0
        output = (stdout2 + stderr2).lower()
        assert 'integrity issues' in output
        assert 'required types' in output


def test_doctor_repairs_missing_notes_file(tmp_path: Path) -> None:
    """Test doctor --repair creates missing required files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Delete notes file
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files) == 1
        notes_file = notes_files[0]
        notes_file.unlink()

        # Run doctor with repair
        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'doctor',
            '--repair',
        ])
        assert exit_code2 == 0
        assert 'valid' in stdout2.lower()
        assert 'repairs performed' in stdout2.lower()
        assert 'created missing' in stdout2.lower()

        # Verify notes file was recreated
        notes_files_after = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files_after) == 1


def test_doctor_detects_duplicate_sqids(tmp_path: Path) -> None:
    """Test doctor detects duplicate SQIDs (filesystem corruption)."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create valid node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Node One',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Manually create another file with same SQID but different MP (filesystem corruption)
        cwd = Path.cwd()
        corrupt_file = cwd / f'200_{sqid}_draft_corrupt.md'
        corrupt_file.write_text('---\ntitle: Corrupt Node\n---\n')

        # Run doctor (should detect duplicate SQID)
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code2 != 0
        output = stdout2 + stderr2
        assert 'integrity issues' in output.lower()
        assert 'duplicate' in output.lower()
        assert sqid in output


def test_doctor_suggests_repair_flag(tmp_path: Path) -> None:
    """Test doctor suggests --repair when issues are detected."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter',
        ])
        assert exit_code1 == 0
        sqid = stdout1.split('@')[1].split(')')[0]

        # Delete notes file
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        notes_files[0].unlink()

        # Run doctor without repair
        exit_code2, stdout2, stderr2 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code2 != 0
        output = stdout2 + stderr2
        assert '--repair' in output


def test_doctor_empty_outline(tmp_path: Path) -> None:
    """Test doctor on empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Run doctor on empty directory
        exit_code, stdout, _stderr = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code == 0
        assert 'valid' in stdout.lower()


def test_doctor_repairs_multiple_nodes(tmp_path: Path) -> None:
    """Test doctor repairs issues across multiple nodes."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create multiple nodes
        exit_code1, stdout1, _stderr1 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter One',
        ])
        assert exit_code1 == 0
        sqid1 = stdout1.split('@')[1].split(')')[0]

        exit_code2, stdout2, _stderr2 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'add',
            'Chapter Two',
        ])
        assert exit_code2 == 0
        sqid2 = stdout2.split('@')[1].split(')')[0]

        # Delete notes files for both
        cwd = Path.cwd()
        for sqid in [sqid1, sqid2]:
            notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
            notes_files[0].unlink()

        # Run doctor with repair
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command([
            'lmk',
            '--directory',
            str(isolated_dir),
            'doctor',
            '--repair',
        ])
        assert exit_code3 == 0
        assert 'valid' in stdout3.lower()

        # Verify both notes files recreated
        notes_files_after = list(cwd.glob('*_notes_*.md'))
        assert len(notes_files_after) == 2


def test_doctor_with_hierarchy(tmp_path: Path) -> None:
    """Test doctor validates hierarchical outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
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

        # Run doctor
        exit_code3, stdout3, _stderr3 = invoke_asyncclick_command(['lmk', '--directory', str(isolated_dir), 'doctor'])
        assert exit_code3 == 0
        assert 'valid' in stdout3.lower()
