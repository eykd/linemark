"""Commander interface for Linemark."""

from __future__ import annotations

from typing import TYPE_CHECKING

from linemark.adapters.filesystem import ConstitutionFileAdapter, FileSystemAdapter
from linemark.adapters.read_type_adapter import ReadTypeAdapter
from linemark.adapters.search_adapter import SearchAdapter
from linemark.adapters.slugifier import SlugifierAdapter
from linemark.adapters.sqid_generator import SQIDGeneratorAdapter
from linemark.adapters.write_type_adapter import WriteTypeAdapter
from linemark.use_cases.add_node import AddNodeUseCase
from linemark.use_cases.compact_outline import CompactOutlineUseCase
from linemark.use_cases.compile_doctype import CompileDoctypeUseCase
from linemark.use_cases.delete_node import DeleteNodeUseCase
from linemark.use_cases.list_outline import ListOutlineUseCase
from linemark.use_cases.manage_types import ManageTypesUseCase
from linemark.use_cases.move_node import MoveNodeUseCase
from linemark.use_cases.read_type import ReadTypeUseCase
from linemark.use_cases.rename_node import RenameNodeUseCase
from linemark.use_cases.search import SearchUseCase
from linemark.use_cases.validate_outline import ValidateOutlineUseCase, ValidationResult
from linemark.use_cases.write_type import WriteTypeUseCase
from linemark.utils import first

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from linemark.domain.entities import Node
    from linemark.ports.search import SearchResult


class ConstitutionCommander:  # pragma: no cover
    """A commander for the Constitution."""

    def __init__(self) -> None:  # pragma: no cover
        self.constitution_file_adapter = ConstitutionFileAdapter()

    async def read_constitution(self, start_path: Path) -> str:  # pragma: no cover
        """Read the constitution."""
        return await self.constitution_file_adapter.read_constitution(start_path)

    async def write_constitution(self, start_path: Path, content: str) -> None:  # pragma: no cover
        """Write the constitution."""
        await self.constitution_file_adapter.write_constitution(start_path, content)


class CharterCommander:  # pragma: no cover
    """A commander for working with a project's charter."""

    async def read_charter(self, start_path: Path) -> str:  # pragma: no cover
        """Read the charter."""
        linemark_commander = LinemarkCommander(start_path)
        first_node = first(await linemark_commander.list_nodes())
        if first_node is None:
            raise ValueError('No nodes found')
        return await linemark_commander.read_type(doctype='charter', sqid=first_node.sqid.value)

    async def write_charter(self, start_path: Path, content: str) -> None:  # pragma: no cover
        """Write the charter."""
        linemark_commander = LinemarkCommander(start_path)
        first_node = first(await linemark_commander.list_nodes())
        if first_node is None:
            first_node = await linemark_commander.add(title='Project')
        return await linemark_commander.write_type(doctype='charter', sqid=first_node.sqid.value, body=content)


class LinemarkCommander:
    """A commander for the Linemark CLI."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    async def compile_doctype(self, doctype: str, sqid: str | None = None, separator: str = '\n\n---\n\n') -> str:
        """Compile all doctype files into a single document.

        Args:
            doctype: The doctype to compile.
            sqid: The SQID of the subtree to compile.
            separator: The separator to use between documents.

        Returns:
            The compiled document.

        Raises:
            DoctypeNotFoundError: If the doctype is not found.
            NodeNotFoundError: If the node is not found.
            OSError: If the file system operation fails.
            PermissionError: If the file system operation fails due to permissions.

        """
        # Strip @ prefix if provided
        clean_sqid = sqid.lstrip('@') if sqid else None

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = CompileDoctypeUseCase(filesystem=filesystem)
        return await use_case.execute(
            doctype=doctype,
            directory=self.directory,
            sqid=clean_sqid,
            separator=separator,
        )

    async def add(
        self,
        title: str,
        child_of: str | None = None,
        sibling_of: str | None = None,
        before: bool = False,  # noqa: FBT001, FBT002
    ) -> Node:
        """Add a new outline node.

        Args:
            title: The title of the new node.
            child_of: The SQID of the parent node.
            sibling_of: The SQID of the sibling node.
            before: Whether to insert before the sibling node.

        Returns:
            The created node.

        Raises:
            ValueError: If the node is not created.
            OSError: If the file system operation fails.
            PermissionError: If the file system operation fails due to permissions.

        """
        # Create adapters
        filesystem = FileSystemAdapter()
        sqid_generator = SQIDGeneratorAdapter()
        slugifier = SlugifierAdapter()

        # Execute use case
        use_case = AddNodeUseCase(
            filesystem=filesystem,
            sqid_generator=sqid_generator,
            slugifier=slugifier,
        )

        return await use_case.execute(
            title=title,
            directory=self.directory,
            parent_sqid=child_of,
            sibling_sqid=sibling_of,
            before=before,
        )

    async def list_nodes(self, sqid: str | None = None) -> list[Node]:
        """List all nodes in the outline, optionally filtered to a subtree.

        Args:
            sqid: The SQID of the node to list.
            show_doctypes: Whether to show document types.
            show_files: Whether to show file paths.

        Returns:
            The list of nodes.

        Raises:
            ValueError: If the nodes are not found.

        """
        filesystem = FileSystemAdapter()

        use_case = ListOutlineUseCase(filesystem=filesystem)
        return await use_case.execute(directory=self.directory, root_sqid=sqid)

    async def move(
        self,
        sqid: str,
        target_mp: str,
    ) -> None:
        """Move a node to a new position in the outline.

        Moves the node with the specified SQID to a new position. All descendants
        are moved automatically with updated paths. SQIDs are preserved.

        Args:
            sqid: The SQID of the node to move.
            target_mp: The target materialized path.
            target_sqid_before: The SQID of the node to insert before.
            target_sqid_after: The SQID of the node to insert after.

        Returns:
            None

        Raises:
            ValueError: If the node is not found.

        """
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = MoveNodeUseCase(filesystem=filesystem)
        await use_case.execute(
            sqid=sqid,
            new_mp_str=target_mp,
            directory=self.directory,
        )

    async def rename(self, sqid: str, new_title: str) -> None:
        r"""Rename a node with a new title.

        Updates the title in the draft file's frontmatter and renames all
        associated files to use the new slug. The SQID and materialized path
        remain unchanged.

        Args:
            sqid: The SQID of the node to rename.
            new_title: The new title of the node.

        Returns:
            None

        Raises:
            ValueError: If the node is not found.

        """
        filesystem = FileSystemAdapter()
        slugifier = SlugifierAdapter()

        # Execute use case
        use_case = RenameNodeUseCase(filesystem=filesystem, slugifier=slugifier)
        await use_case.execute(sqid=sqid, new_title=new_title, directory=self.directory)

    async def delete(self, sqid: str, recursive: bool, promote: bool) -> list[Node]:  # noqa: FBT001
        """Delete a node from the outline.

        By default, only deletes leaf nodes (nodes without children).
        Use recursive to delete node and all descendants.
        Use promote to delete node but promote children to parent level.

        Args:
            sqid: The SQID of the node to delete.
            recursive: Whether to delete the node and all descendants.
            promote: Whether to delete the node but promote children to parent level.

        Returns:
            The list of deleted nodes.

        Raises:
            ValueError: If the node is not found.
            OSError: If the file system operation fails.
            PermissionError: If the file system operation fails due to permissions.

        """
        filesystem = FileSystemAdapter()
        use_case = DeleteNodeUseCase(filesystem=filesystem)
        return await use_case.execute(sqid=sqid, directory=self.directory, recursive=recursive, promote=promote)

    async def compact(self, sqid: str | None) -> list[Node]:
        """Restore clean, evenly-spaced numbering to the outline.

        Renumbers siblings at the specified level with even spacing (100s/10s/1s tier).
        If SQID provided, compacts children of that node. Otherwise compacts root level.

        Args:
            sqid: The SQID of the node to compact.

        Returns:
            The list of compacted nodes.

        Raises:
            ValueError: If the node is not found.

        """
        filesystem = FileSystemAdapter()
        use_case = CompactOutlineUseCase(filesystem=filesystem)
        return await use_case.execute(sqid=sqid, directory=self.directory)

    async def doctor(self, repair: bool) -> ValidationResult:  # noqa: FBT001
        """Validate outline integrity and repair common issues.

        Checks for duplicate SQIDs, missing required files, and other integrity issues.
        With repair flag, automatically fixes common problems like missing draft/notes files.

        Args:
            repair: Whether to repair common issues.

        Returns:
            The validation result.

        Raises:
            ValueError: If the outline is not valid.

        """
        filesystem = FileSystemAdapter()
        use_case = ValidateOutlineUseCase(filesystem=filesystem)
        return await use_case.execute(directory=self.directory, repair=repair)

    async def search(
        self,
        pattern: str,
        subtree_sqid: str | None,
        doctypes: list[str] | None,
        case_sensitive: bool,  # noqa: FBT001
        multiline: bool,  # noqa: FBT001
        literal: bool,  # noqa: FBT001
    ) -> AsyncIterator[SearchResult]:
        """Search for patterns across the outline.

        Search for regex or literal patterns across document type files,
        with optional filtering by subtree and doctype. Results are returned
        in outline order.

        Args:
            pattern: The pattern to search for.
            subtree_sqid: The SQID of the subtree to search.
            doctypes: The document types to search.
            case_sensitive: Whether to search case-sensitively.
            multiline: Whether to search multiline.
            literal: Whether to search literally.
            output_json: Whether to output as JSON.

        Returns:
            The list of search results.

        Raises:
            InvalidRegexError: If the pattern is invalid.
            FileNotFoundError: If the directory does not exist.
            PermissionError: If the files are not readable.
            UnicodeDecodeError: If the files are not valid UTF-8.

        """
        search_adapter = SearchAdapter()
        use_case = SearchUseCase(search_port=search_adapter)
        async for result in use_case.execute(
            pattern=pattern,
            directory=self.directory,
            subtree_sqid=subtree_sqid,
            doctypes=doctypes,
            case_sensitive=case_sensitive,
            multiline=multiline,
            literal=literal,
        ):
            yield result

    async def list_types(self, sqid: str) -> list[str]:
        """List all document types for a node.

        Shows all document types associated with the specified node SQID.

        Args:
            sqid: The SQID of the node to list document types for.

        Returns:
            The list of document types.

        Raises:
            ValueError: If the document types are not found.

        """
        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        return await use_case.list_types(sqid=sqid, directory=self.directory)

    async def add_type(self, doc_type: str, sqid: str) -> None:
        """Add a new document type to a node.

        Args:
            doc_type: The document type to add.
            sqid: The SQID of the node to add the document type to.

        Returns:
            None

        Raises:
            ValueError: If the document type is not added.

        """
        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        return await use_case.add_type(sqid=sqid, doc_type=doc_type, directory=self.directory)

    async def remove_type(self, doc_type: str, sqid: str) -> None:
        """Remove a document type from a node.

        Deletes the file for the specified document type.
        Required types (draft, notes) cannot be removed.

        Args:
            doc_type: The document type to remove.
            sqid: The SQID of the node to remove the document type from.

        Returns:
            None

        Raises:
            ValueError: If the document type is not removed.

        """
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        return await use_case.remove_type(sqid=sqid, doc_type=doc_type, directory=self.directory)

    async def read_type(self, doctype: str, sqid: str) -> str:
        """Read the body content of a document type.

        Read the body of the file for the specified document type.

        Args:
            doctype: The document type to read.
            sqid: The SQID of the node to read the document type from.

        Returns:
            The body content of the document type.

        Raises:
            ValueError: If the document type is not read.

        """
        read_adapter = ReadTypeAdapter()

        # Execute use case
        use_case = ReadTypeUseCase(read_type_port=read_adapter)
        return await use_case.execute(
            sqid=sqid,
            doctype=doctype,
            directory=self.directory,
        )

    async def write_type(self, doctype: str, sqid: str, body: str) -> None:
        """Write body content to a document type from stdin.

        Write the body content from stdin to the specified document type file,
        preserving existing YAML frontmatter. The write is atomic using a
        temporary file and rename operation.

        Args:
            doctype: The document type to write.
            sqid: The SQID of the node to write the document type to.
            body: The body content to write.

        Returns:
            None

        Raises:
            ValueError: If the document type is not written.

        """
        # Create adapter
        write_adapter = WriteTypeAdapter()

        # Execute use case
        use_case = WriteTypeUseCase(write_type_port=write_adapter)
        return use_case.execute(
            sqid=sqid,
            doctype=doctype,
            body=body,
            directory=self.directory,
        )
