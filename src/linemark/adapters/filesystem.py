"""FileSystem adapter implementation.

Concrete implementation of FileSystemPort using pathlib for file operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class FileSystemAdapter:
    """Concrete filesystem adapter using pathlib.

    Implements FileSystemPort protocol using Python's pathlib library.
    All file operations are synchronous and use UTF-8 encoding.
    """

    def read_file(self, filepath: Path) -> str:  # noqa: PLR6301
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
        return filepath.read_text(encoding='utf-8')

    def write_file(self, filepath: Path, content: str) -> None:  # noqa: PLR6301
        """Write string content to file, creating parent directories if needed.

        Args:
            filepath: Absolute path to file
            content: UTF-8 string content

        Raises:
            PermissionError: If file/directory not writable
            OSError: For other filesystem errors

        """
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding='utf-8')

    def delete_file(self, filepath: Path) -> None:  # noqa: PLR6301
        """Delete file if it exists.

        Args:
            filepath: Absolute path to file

        Raises:
            PermissionError: If file not deletable
            OSError: For other filesystem errors

        """
        if filepath.exists():
            filepath.unlink()

    def rename_file(self, old_path: Path, new_path: Path) -> None:  # noqa: PLR6301
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
        if not old_path.exists():
            msg = f'File not found: {old_path}'
            raise FileNotFoundError(msg)

        if new_path.exists():
            msg = f'File already exists: {new_path}'
            raise FileExistsError(msg)

        old_path.rename(new_path)

    def list_markdown_files(self, directory: Path) -> list[Path]:  # noqa: PLR6301
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
        if not directory.exists():
            msg = f'Directory not found: {directory}'
            raise FileNotFoundError(msg)

        if not directory.is_dir():
            msg = f'Not a directory: {directory}'
            raise NotADirectoryError(msg)

        return sorted(directory.glob('*.md'))

    def file_exists(self, filepath: Path) -> bool:  # noqa: PLR6301
        """Check if file exists.

        Args:
            filepath: Path to check

        Returns:
            True if file exists and is a regular file

        """
        return filepath.exists() and filepath.is_file()

    def create_directory(self, directory: Path) -> None:  # noqa: PLR6301
        """Create directory and all parent directories.

        Args:
            directory: Directory path to create

        Raises:
            PermissionError: If cannot create directory
            FileExistsError: If path exists and is not a directory
            OSError: For other filesystem errors

        """
        if directory.exists() and not directory.is_dir():
            msg = f'Path exists but is not a directory: {directory}'
            raise FileExistsError(msg)

        directory.mkdir(parents=True, exist_ok=True)
