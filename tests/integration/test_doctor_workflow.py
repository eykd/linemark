"""Integration tests for doctor (validate/repair) workflow."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from linemark.cli.main import lmk


def test_doctor_validates_clean_outline(tmp_path: Path) -> None:
    """Test doctor command on valid outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create valid outline
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0

        # Run doctor
        result3 = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'valid' in result3.output.lower()


def test_doctor_detects_missing_notes_file(tmp_path: Path) -> None:
    """Test doctor detects missing required files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        result1 = runner.invoke(lmk, ['add', 'Chapter', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Delete notes file to create invalid state
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files) == 1
        notes_files[0].unlink()

        # Run doctor (should detect issue)
        result2 = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result2.exit_code != 0
        assert 'integrity issues' in result2.output.lower()
        assert 'required types' in result2.output.lower()


def test_doctor_repairs_missing_notes_file(tmp_path: Path) -> None:
    """Test doctor --repair creates missing required files."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        result1 = runner.invoke(lmk, ['add', 'Chapter', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Delete notes file
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files) == 1
        notes_file = notes_files[0]
        notes_file.unlink()

        # Run doctor with repair
        result2 = runner.invoke(lmk, ['doctor', '--repair', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        assert 'valid' in result2.output.lower()
        assert 'repairs performed' in result2.output.lower()
        assert 'created missing' in result2.output.lower()

        # Verify notes file was recreated
        notes_files_after = list(cwd.glob(f'*{sqid}_notes*.md'))
        assert len(notes_files_after) == 1


def test_doctor_detects_duplicate_sqids(tmp_path: Path) -> None:
    """Test doctor detects duplicate SQIDs (filesystem corruption)."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create valid node
        result1 = runner.invoke(lmk, ['add', 'Node One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Manually create another file with same SQID but different MP (filesystem corruption)
        cwd = Path.cwd()
        corrupt_file = cwd / f'200_{sqid}_draft_corrupt.md'
        corrupt_file.write_text('---\ntitle: Corrupt Node\n---\n')

        # Run doctor (should detect duplicate SQID)
        result2 = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result2.exit_code != 0
        assert 'integrity issues' in result2.output.lower()
        assert 'duplicate' in result2.output.lower()
        assert sqid in result2.output


def test_doctor_suggests_repair_flag(tmp_path: Path) -> None:
    """Test doctor suggests --repair when issues are detected."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create node
        result1 = runner.invoke(lmk, ['add', 'Chapter', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid = result1.output.split('@')[1].split(')')[0]

        # Delete notes file
        cwd = Path.cwd()
        notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
        notes_files[0].unlink()

        # Run doctor without repair
        result2 = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result2.exit_code != 0
        assert '--repair' in result2.output


def test_doctor_empty_outline(tmp_path: Path) -> None:
    """Test doctor on empty outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Run doctor on empty directory
        result = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result.exit_code == 0
        assert 'valid' in result.output.lower()


def test_doctor_repairs_multiple_nodes(tmp_path: Path) -> None:
    """Test doctor repairs issues across multiple nodes."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create multiple nodes
        result1 = runner.invoke(lmk, ['add', 'Chapter One', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        sqid1 = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(lmk, ['add', 'Chapter Two', '--directory', str(isolated_dir)])
        assert result2.exit_code == 0
        sqid2 = result2.output.split('@')[1].split(')')[0]

        # Delete notes files for both
        cwd = Path.cwd()
        for sqid in [sqid1, sqid2]:
            notes_files = list(cwd.glob(f'*{sqid}_notes*.md'))
            notes_files[0].unlink()

        # Run doctor with repair
        result3 = runner.invoke(lmk, ['doctor', '--repair', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'valid' in result3.output.lower()

        # Verify both notes files recreated
        notes_files_after = list(cwd.glob('*_notes_*.md'))
        assert len(notes_files_after) == 2


def test_doctor_with_hierarchy(tmp_path: Path) -> None:
    """Test doctor validates hierarchical outline."""
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path) as isolated_dir:
        # Create hierarchy
        result1 = runner.invoke(lmk, ['add', 'Parent', '--directory', str(isolated_dir)])
        assert result1.exit_code == 0
        parent_sqid = result1.output.split('@')[1].split(')')[0]

        result2 = runner.invoke(
            lmk,
            ['add', 'Child', '--child-of', f'@{parent_sqid}', '--directory', str(isolated_dir)],
        )
        assert result2.exit_code == 0

        # Run doctor
        result3 = runner.invoke(lmk, ['doctor', '--directory', str(isolated_dir)])
        assert result3.exit_code == 0
        assert 'valid' in result3.output.lower()
