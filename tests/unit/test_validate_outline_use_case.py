"""Unit tests for ValidateOutlineUseCase."""

from __future__ import annotations

from pathlib import Path

import pytest


class FakeFileSystem:
    """Fake filesystem adapter for testing."""

    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    async def read_file(self, path: Path) -> str:
        return self.files.get(str(path), '')

    async def write_file(self, path: Path, content: str) -> None:
        self.files[str(path)] = content

    async def delete_file(self, path: Path) -> None:
        if str(path) in self.files:
            del self.files[str(path)]

    async def list_markdown_files(self, directory: Path) -> list[Path]:
        return [Path(path) for path in self.files if path.endswith('.md') and path.startswith(str(directory))]

    async def file_exists(self, path: Path) -> bool:
        return str(path) in self.files

    async def create_directory(self, directory: Path) -> None:
        """Create directory (no-op for fake filesystem)."""

    async def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]


@pytest.mark.asyncio
async def test_validate_clean_outline() -> None:
    """Test validating an outline with no issues."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create valid outline
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '100_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '200_SQID2_draft_node-two.md')] = '---\ntitle: Node Two\n---'
    fs.files[str(directory / '200_SQID2_notes_node-two.md')] = ''

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate outline
    result = await use_case.execute(directory=directory, repair=False)

    # Should have no violations
    assert result['valid'] is True
    assert len(result['violations']) == 0
    assert len(result['repaired']) == 0


@pytest.mark.asyncio
async def test_validate_detects_missing_required_types() -> None:
    """Test detecting missing draft or notes files."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node missing notes file
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    # Missing notes file

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate outline
    result = await use_case.execute(directory=directory, repair=False)

    # Should detect missing required type
    assert result['valid'] is False
    assert len(result['violations']) > 0
    assert any('required types' in v.lower() for v in result['violations'])


@pytest.mark.asyncio
async def test_validate_repairs_missing_required_types() -> None:
    """Test auto-repairing missing draft or notes files."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create node missing notes file
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate with repair
    result = await use_case.execute(directory=directory, repair=True)

    # Should repair the issue
    assert len(result['repaired']) > 0
    assert any('created missing' in r.lower() for r in result['repaired'])

    # Verify notes file was created
    assert str(directory / '100_SQID1_notes_node-one.md') in fs.files


@pytest.mark.asyncio
async def test_validate_detects_duplicate_sqids() -> None:
    """Test detecting duplicate SQIDs (shouldn't happen normally)."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create two nodes with same SQID (invalid state)
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '100_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '200_SQID1_draft_node-two.md')] = '---\ntitle: Node Two\n---'
    fs.files[str(directory / '200_SQID1_notes_node-two.md')] = ''

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate outline
    result = await use_case.execute(directory=directory, repair=False)

    # Should detect duplicate SQIDs
    assert result['valid'] is False
    assert len(result['violations']) > 0
    assert any('duplicate' in v.lower() and 'sqid' in v.lower() for v in result['violations'])


@pytest.mark.asyncio
async def test_validate_detects_duplicate_mps() -> None:
    """Test detecting duplicate materialized paths (shouldn't happen normally)."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create two nodes with same MP but different SQIDs (invalid state)
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '100_SQID1_notes_node-one.md')] = ''
    fs.files[str(directory / '100_SQID2_draft_node-two.md')] = '---\ntitle: Node Two\n---'
    fs.files[str(directory / '100_SQID2_notes_node-two.md')] = ''

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate outline
    result = await use_case.execute(directory=directory, repair=False)

    # Should detect duplicate MPs
    assert result['valid'] is False
    assert len(result['violations']) > 0
    assert any('duplicate' in v.lower() and 'path' in v.lower() for v in result['violations'])


@pytest.mark.asyncio
async def test_validate_empty_outline() -> None:
    """Test validating an empty outline."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate empty outline
    result = await use_case.execute(directory=directory, repair=False)

    # Empty outline is valid
    assert result['valid'] is True
    assert len(result['violations']) == 0


@pytest.mark.asyncio
async def test_validate_returns_repair_summary() -> None:
    """Test that validation returns summary of repairs performed."""
    from linemark.use_cases.validate_outline import ValidateOutlineUseCase

    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes with missing files
    fs.files[str(directory / '100_SQID1_draft_node-one.md')] = '---\ntitle: Node One\n---'
    fs.files[str(directory / '200_SQID2_draft_node-two.md')] = '---\ntitle: Node Two\n---'

    use_case = ValidateOutlineUseCase(filesystem=fs)

    # Validate with repair
    result = await use_case.execute(directory=directory, repair=True)

    # Should report repairs
    assert 'repaired' in result
    assert len(result['repaired']) == 2  # Two notes files created
    assert 'violations' in result
    assert 'valid' in result
