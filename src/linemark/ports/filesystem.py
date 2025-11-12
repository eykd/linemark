"""FileSystem Port Contract.

This module defines the abstract interface for filesystem operations required
by Linemark. The port isolates domain logic from concrete filesystem implementation,
enabling testing with fake adapters and future alternative storage backends.

Constitutional Alignment:
- Hexagonal Architecture (§ I): Port defines boundary between domain and infrastructure
- Test-First Development (§ II): Contract testable independently of implementation
- Plain Text Storage (§ IV): Interface assumes markdown files with YAML frontmatter
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path


class FileSystemPort(Protocol):
    """Port for filesystem operations.

    This protocol defines the contract that filesystem adapters must implement.
    All methods should raise descriptive exceptions on filesystem errors (per FR-042).
    """

    def read_file(self, filepath: Path) -> str:
        """Read file contents as string.

        Args:
            filepath: Absolute path to file

        Returns:
            File contents as UTF-8 string

        Raises:
            FileNotFoundError: If file does not exist
            PermissionError: If file is not readable
            OSError: For other filesystem errors (disk full, locked file, etc.)

        """
        ...

    def write_file(self, filepath: Path, content: str) -> None:
        """Write string content to file, creating parent directories if needed.

        Args:
            filepath: Absolute path to file
            content: UTF-8 string content

        Raises:
            PermissionError: If file/directory not writable
            OSError: For other filesystem errors (disk full, locked file, etc.)

        """
        ...

    def delete_file(self, filepath: Path) -> None:
        """Delete file if it exists.

        Args:
            filepath: Absolute path to file

        Raises:
            PermissionError: If file not deletable
            OSError: For other filesystem errors (file locked, etc.)

        Note:
            If file does not exist, this is a no-op (not an error).

        """
        ...

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Atomically rename file.

        Args:
            old_path: Current file path
            new_path: Target file path

        Raises:
            FileNotFoundError: If old_path does not exist
            FileExistsError: If new_path already exists
            PermissionError: If rename not permitted
            OSError: For other filesystem errors

        Note:
            Implementation must use atomic rename operations where possible
            (Path.rename on POSIX, MoveFileEx on Windows).

        """
        ...

    def list_markdown_files(self, directory: Path) -> list[Path]:
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
        ...

    def file_exists(self, filepath: Path) -> bool:
        """Check if file exists.

        Args:
            filepath: Path to check

        Returns:
            True if file exists and is a regular file

        Note:
            Returns False for directories, symlinks, and non-existent paths.
            Does not raise exceptions.

        """
        ...

    def create_directory(self, directory: Path) -> None:
        """Create directory and all parent directories.

        Args:
            directory: Directory path to create

        Raises:
            PermissionError: If cannot create directory
            FileExistsError: If path exists and is not a directory
            OSError: For other filesystem errors

        Note:
            If directory already exists, this is a no-op (not an error).

        """
        ...
