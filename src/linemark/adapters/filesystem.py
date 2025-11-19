"""FileSystem adapter implementation.

Concrete implementation of FileSystemPort using anyio for async file operations.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import anyio

if TYPE_CHECKING:
    from pathlib import Path


class ConstitutionFileAdapter:  # pragma: no cover
    """Concrete filesystem adapter for constitution files."""

    def __init__(self) -> None:  # pragma: no cover
        self.file_adapter = FileSystemAdapter()

    async def find_constitution_file(self, start_path: Path) -> Path:  # pragma: no cover
        """Find the constitution file starting from the given path.

        Args:
            start_path: Path to start searching from

        Returns:
            Path to the constitution file. (This path may or may not exist.)

        """
        start_anyio = anyio.Path(start_path)
        if await start_anyio.is_file() and start_path.name == 'constitution.md':
            return start_path

        path = start_path

        while True:
            constitution_file = path / 'constitution.md'
            constitution_anyio = anyio.Path(constitution_file)
            if await constitution_anyio.exists() and os.access(constitution_file, os.R_OK):
                return constitution_file
            path = path.parent
            if str(path) == path.anchor or not os.access(path, os.R_OK) or not os.access(path, os.W_OK):
                break

        return start_path / 'constitution.md'

    async def read_constitution(self, start_path: Path) -> str:  # pragma: no cover
        """Read the governing constitution document starting from the given path.

        Args:
            start_path: Path to start searching from

        Returns:
            Constitution file contents

        Raises:
            FileNotFoundError: If the constitution file is not found

        """
        constitution_file = await self.find_constitution_file(start_path)
        constitution_anyio = anyio.Path(constitution_file)
        if not await constitution_anyio.exists():
            raise FileNotFoundError('Constitution file not found')
        return await self.file_adapter.read_file(constitution_file)

    async def write_constitution(self, start_path: Path, content: str) -> Path:  # pragma: no cover
        """Write the governing constitution document starting from the given path.

        Args:
            start_path: Path to start searching from
            content: Constitution file contents

        """
        constitution_file = await self.find_constitution_file(start_path)
        await self.file_adapter.write_file(constitution_file, content)
        return constitution_file


class FileSystemAdapter:
    """Concrete filesystem adapter using anyio.

    Implements FileSystemPort protocol using anyio's async Path operations.
    All file operations are asynchronous and use UTF-8 encoding.
    """

    async def read_file(self, filepath: Path) -> str:
        """Read file contents as string.

        Args:
            filepath: Absolute path to file

        Returns:
            File contents as UTF-8 string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file is not readable
            OSError: For other filesystem errors

        """
        return await anyio.Path(filepath).read_text(encoding='utf-8')

    async def write_file(self, filepath: Path, content: str) -> None:
        """Write string content to file, creating parent directories if needed.

        Args:
            filepath: Absolute path to file
            content: UTF-8 string content

        Raises:
            PermissionError: If file/directory not writable
            OSError: For other filesystem errors

        """
        parent_anyio = anyio.Path(filepath.parent)
        await parent_anyio.mkdir(parents=True, exist_ok=True)
        await anyio.Path(filepath).write_text(content, encoding='utf-8')

    async def delete_file(self, filepath: Path) -> None:
        """Delete file if it exists.

        Args:
            filepath: Absolute path to file

        Raises:
            PermissionError: If file not deletable
            OSError: For other filesystem errors

        """
        filepath_anyio = anyio.Path(filepath)
        if await filepath_anyio.exists():
            await filepath_anyio.unlink()

    async def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Atomically rename file.

        Args:
            old_path: Current file path
            new_path: Target file path

        Raises:
            FileNotFoundError: If old_path does not exist
            FileExistsError: If new_path already exists
            PermissionError: If rename not permitted
            OSError: For other filesystem errors

        """
        old_anyio = anyio.Path(old_path)
        new_anyio = anyio.Path(new_path)

        if not await old_anyio.exists():
            msg = f'File not found: {old_path}'
            raise FileNotFoundError(msg)

        if await new_anyio.exists():
            msg = f'File already exists: {new_path}'
            raise FileExistsError(msg)

        await old_anyio.rename(new_path)

    async def list_markdown_files(self, directory: Path) -> list[Path]:
        """List all .md files in directory (non-recursive).

        Args:
            directory: Directory to scan

        Returns:
            List of absolute paths to .md files

        Raises:
            FileNotFoundError: If directory does not exist
            PermissionError: If directory not readable
            NotADirectoryError: If path is not a directory

        """
        directory_anyio = anyio.Path(directory)

        if not await directory_anyio.exists():
            msg = f'Directory not found: {directory}'
            raise FileNotFoundError(msg)

        if not await directory_anyio.is_dir():
            msg = f'Not a directory: {directory}'
            raise NotADirectoryError(msg)

        # Convert async iterator to list and sort
        # Convert anyio.Path back to pathlib.Path for return type compatibility
        from pathlib import Path as PathlibPath

        files = [PathlibPath(p) async for p in directory_anyio.glob('*.md')]
        return sorted(files)

    async def file_exists(self, filepath: Path) -> bool:
        """Check if file exists.

        Args:
            filepath: Path to check

        Returns:
            True if file exists and is a regular file

        """
        filepath_anyio = anyio.Path(filepath)
        return await filepath_anyio.exists() and await filepath_anyio.is_file()

    async def create_directory(self, directory: Path) -> None:
        """Create directory and all parent directories.

        Args:
            directory: Directory path to create

        Raises:
            PermissionError: If cannot create directory
            FileExistsError: If path exists and is not a directory
            OSError: For other filesystem errors

        """
        directory_anyio = anyio.Path(directory)

        if await directory_anyio.exists() and not await directory_anyio.is_dir():
            msg = f'Path exists but is not a directory: {directory}'
            raise FileExistsError(msg)

        await directory_anyio.mkdir(parents=True, exist_ok=True)
