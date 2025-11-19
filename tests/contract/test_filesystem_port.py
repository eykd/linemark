"""Contract tests for FileSystemPort implementations.

These tests verify that any concrete implementation of FileSystemPort
follows the protocol contract correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort


class TestFileSystemPortContract:
    """Contract tests for FileSystemPort protocol.

    To test an implementation, create a test class that inherits from this
    and provides a filesystem_port fixture.
    """

    # Mark as non-collection to avoid pytest discovering this base class
    __test__ = False

    @pytest.mark.asyncio
    async def test_write_and_read_file(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Write a file and read it back."""
        filepath = tmp_path / 'test.md'
        content = '# Test Content\n\nThis is a test.'

        await filesystem_port.write_file(filepath, content)
        result = await filesystem_port.read_file(filepath)

        assert result == content

    @pytest.mark.asyncio
    async def test_read_nonexistent_file_raises_error(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Reading nonexistent file raises FileNotFoundError."""
        filepath = tmp_path / 'nonexistent.md'

        with pytest.raises(FileNotFoundError):
            await filesystem_port.read_file(filepath)

    @pytest.mark.asyncio
    async def test_write_file_creates_parent_directories(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Writing a file creates parent directories if needed."""
        filepath = tmp_path / 'parent' / 'child' / 'test.md'
        content = 'test content'

        await filesystem_port.write_file(filepath, content)

        assert filepath.exists()
        assert await filesystem_port.read_file(filepath) == content

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Delete an existing file."""
        filepath = tmp_path / 'test.md'
        await filesystem_port.write_file(filepath, 'content')

        await filesystem_port.delete_file(filepath)

        assert not await filesystem_port.file_exists(filepath)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file_is_noop(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Deleting nonexistent file does not raise error."""
        filepath = tmp_path / 'nonexistent.md'

        # Should not raise
        await filesystem_port.delete_file(filepath)

    @pytest.mark.asyncio
    async def test_rename_file(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Rename a file atomically."""
        old_path = tmp_path / 'old.md'
        new_path = tmp_path / 'new.md'
        content = 'test content'

        await filesystem_port.write_file(old_path, content)
        await filesystem_port.rename_file(old_path, new_path)

        assert await filesystem_port.file_exists(new_path)
        assert not await filesystem_port.file_exists(old_path)
        assert await filesystem_port.read_file(new_path) == content

    @pytest.mark.asyncio
    async def test_rename_nonexistent_file_raises_error(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Renaming nonexistent file raises FileNotFoundError."""
        old_path = tmp_path / 'nonexistent.md'
        new_path = tmp_path / 'new.md'

        with pytest.raises(FileNotFoundError):
            await filesystem_port.rename_file(old_path, new_path)

    @pytest.mark.asyncio
    async def test_rename_to_existing_file_raises_error(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Renaming to existing file raises FileExistsError."""
        old_path = tmp_path / 'old.md'
        new_path = tmp_path / 'existing.md'

        await filesystem_port.write_file(old_path, 'old content')
        await filesystem_port.write_file(new_path, 'existing content')

        with pytest.raises(FileExistsError):
            await filesystem_port.rename_file(old_path, new_path)

    @pytest.mark.asyncio
    async def test_list_markdown_files(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """List all .md files in directory."""
        await filesystem_port.write_file(tmp_path / 'file1.md', 'content1')
        await filesystem_port.write_file(tmp_path / 'file2.md', 'content2')
        await filesystem_port.write_file(tmp_path / 'file3.txt', 'not markdown')

        files = await filesystem_port.list_markdown_files(tmp_path)

        assert len(files) == 2
        assert tmp_path / 'file1.md' in files
        assert tmp_path / 'file2.md' in files
        assert tmp_path / 'file3.txt' not in files

    @pytest.mark.asyncio
    async def test_list_markdown_files_empty_directory(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """List markdown files in empty directory returns empty list."""
        files = await filesystem_port.list_markdown_files(tmp_path)

        assert files == []

    @pytest.mark.asyncio
    async def test_list_markdown_files_nonexistent_directory_raises_error(
        self, filesystem_port: FileSystemPort, tmp_path: Path
    ) -> None:
        """Listing files in nonexistent directory raises FileNotFoundError."""
        nonexistent = tmp_path / 'nonexistent'

        with pytest.raises(FileNotFoundError):
            await filesystem_port.list_markdown_files(nonexistent)

    @pytest.mark.asyncio
    async def test_file_exists_true_for_existing_file(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """file_exists returns True for existing file."""
        filepath = tmp_path / 'test.md'
        await filesystem_port.write_file(filepath, 'content')

        assert await filesystem_port.file_exists(filepath) is True

    @pytest.mark.asyncio
    async def test_file_exists_false_for_nonexistent_file(
        self, filesystem_port: FileSystemPort, tmp_path: Path
    ) -> None:
        """file_exists returns False for nonexistent file."""
        filepath = tmp_path / 'nonexistent.md'

        assert await filesystem_port.file_exists(filepath) is False

    @pytest.mark.asyncio
    async def test_file_exists_false_for_directory(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """file_exists returns False for directories."""
        directory = tmp_path / 'testdir'
        await filesystem_port.create_directory(directory)

        assert await filesystem_port.file_exists(directory) is False

    @pytest.mark.asyncio
    async def test_create_directory(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Create directory and all parents."""
        directory = tmp_path / 'parent' / 'child' / 'grandchild'

        await filesystem_port.create_directory(directory)

        assert directory.exists()
        assert directory.is_dir()

    @pytest.mark.asyncio
    async def test_create_existing_directory_is_noop(self, filesystem_port: FileSystemPort, tmp_path: Path) -> None:
        """Creating existing directory does not raise error."""
        directory = tmp_path / 'testdir'
        directory.mkdir()

        # Should not raise
        await filesystem_port.create_directory(directory)

    @pytest.mark.asyncio
    async def test_list_markdown_files_on_file_raises_error(
        self, filesystem_port: FileSystemPort, tmp_path: Path
    ) -> None:
        """Listing markdown files on a file path raises NotADirectoryError."""
        filepath = tmp_path / 'test.md'
        await filesystem_port.write_file(filepath, 'content')

        with pytest.raises(NotADirectoryError):
            await filesystem_port.list_markdown_files(filepath)

    @pytest.mark.asyncio
    async def test_create_directory_when_path_is_file_raises_error(
        self, filesystem_port: FileSystemPort, tmp_path: Path
    ) -> None:
        """Creating directory when path exists as a file raises FileExistsError."""
        filepath = tmp_path / 'test.md'
        await filesystem_port.write_file(filepath, 'content')

        with pytest.raises(FileExistsError):
            await filesystem_port.create_directory(filepath)
