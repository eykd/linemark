"""Command-line interface for Linemark."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from linemark.adapters.filesystem import FileSystemAdapter
from linemark.adapters.slugifier import SlugifierAdapter
from linemark.adapters.sqid_generator import SQIDGeneratorAdapter
from linemark.cli.formatters import format_json, format_tree
from linemark.domain.exceptions import DoctypeNotFoundError, NodeNotFoundError
from linemark.use_cases.add_node import AddNodeUseCase
from linemark.use_cases.compact_outline import CompactOutlineUseCase
from linemark.use_cases.compile_doctype import CompileDoctypeUseCase
from linemark.use_cases.delete_node import DeleteNodeUseCase
from linemark.use_cases.list_outline import ListOutlineUseCase
from linemark.use_cases.manage_types import ManageTypesUseCase
from linemark.use_cases.move_node import MoveNodeUseCase
from linemark.use_cases.rename_node import RenameNodeUseCase
from linemark.use_cases.validate_outline import ValidateOutlineUseCase


@click.group()
def lmk() -> None:
    """Linemark - Hierarchical Markdown Outline Manager.

    A command-line tool for managing hierarchical outlines of Markdown documents
    using filename-based organization.
    """


@lmk.command()
@click.argument('doctype')
@click.argument('sqid', required=False)
@click.option(
    '--separator',
    default='\n\n---\n\n',
    help='Separator between documents (escape sequences interpreted)',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def compile(  # noqa: A001
    doctype: str,
    sqid: str | None,
    separator: str,
    directory: Path,
) -> None:
    """Compile all doctype files into a single document.

    Concatenates content from all nodes containing the specified DOCTYPE,
    traversing in hierarchical order (depth-first). Optionally filter to a
    specific subtree by providing a SQID.

    \b
    Examples:
        \b
        # Compile all draft files
        lmk compile draft

    \b
        # Compile notes from specific subtree
        lmk compile notes @Gxn7qZp

    \b
        # Use custom separator
        lmk compile draft --separator "===PAGE BREAK==="

    \b
        # Save to file
        lmk compile draft > compiled.md

    """
    try:
        # Strip @ prefix if provided
        clean_sqid = sqid.lstrip('@') if sqid else None

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = CompileDoctypeUseCase(filesystem=filesystem)
        result = use_case.execute(
            doctype=doctype,
            directory=directory,
            sqid=clean_sqid,
            separator=separator,
        )

        # Output to stdout
        if result:
            click.echo(result)
        # Empty result is silent success (no output)

    except DoctypeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except NodeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except (OSError, PermissionError) as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(2)  # pragma: no cover


@lmk.command()
@click.argument('title')
@click.option(
    '--child-of',
    help='Parent node SQID (@SQID format)',
    metavar='SQID',
)
@click.option(
    '--sibling-of',
    help='Sibling node SQID (@SQID format)',
    metavar='SQID',
)
@click.option(
    '--before',
    is_flag=True,
    help='Insert before sibling (requires --sibling-of)',
)
@click.option(
    '--after',
    is_flag=True,
    help='Insert after sibling (requires --sibling-of)',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def add(
    title: str,
    child_of: str | None,
    sibling_of: str | None,
    before: bool,  # noqa: FBT001
    after: bool,  # noqa: ARG001, FBT001
    directory: Path,
) -> None:
    """Add a new outline node.

    Creates a new node with the specified TITLE. By default, adds a root-level
    node. Use --child-of to create a child node, or --sibling-of with --before
    or --after to position relative to an existing node.

    \b
    Examples:
        \b
        # Add a root-level chapter
        lmk add "Chapter One"

    \b
        # Add a child section
        lmk add "Section 1.1" --child-of @SQID1

    \b
        # Add before an existing node
        lmk add "Prologue" --sibling-of @SQID1 --before

    """
    try:
        # Strip @ prefix if provided
        parent_sqid = child_of.lstrip('@') if child_of else None
        sibling_sqid = sibling_of.lstrip('@') if sibling_of else None

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

        node = use_case.execute(
            title=title,
            directory=directory,
            parent_sqid=parent_sqid,
            sibling_sqid=sibling_sqid,
            before=before,
        )

        # Output success message
        click.echo(f'Created node {node.mp.as_string} (@{node.sqid.value}): {node.title}')
        click.echo(f'  Draft: {node.filename("draft")}')
        click.echo(f'  Notes: {node.filename("notes")}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output in JSON format instead of tree',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def list(output_json: bool, directory: Path) -> None:  # noqa: A001, FBT001
    """List all nodes in the outline.

    Displays the outline as a tree structure by default, or as nested JSON
    with --json flag.

    \b
    Examples:
        \b
        # Show tree structure
        lmk list

    \b
        # Show JSON structure
        lmk list --json

    """
    try:
        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ListOutlineUseCase(filesystem=filesystem)
        nodes = use_case.execute(directory=directory)

        # Format and output
        output = format_json(nodes) if output_json else format_tree(nodes)

        if output:
            click.echo(output)
        else:
            click.echo('No nodes found in outline.', err=True)

    except ValueError as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


@lmk.command()
@click.argument('sqid')
@click.option(
    '--to',
    'target_mp',
    required=True,
    help='Target materialized path (e.g., 200-100) or parent SQID with @',
    metavar='PATH',
)
@click.option(
    '--before',
    'target_sqid_before',
    help='Insert before this SQID (requires --to to be parent)',
    metavar='SQID',
)
@click.option(
    '--after',
    'target_sqid_after',
    help='Insert after this SQID (requires --to to be parent)',
    metavar='SQID',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def move(
    sqid: str,
    target_mp: str,
    target_sqid_before: str | None,  # noqa: ARG001
    target_sqid_after: str | None,  # noqa: ARG001
    directory: Path,
) -> None:
    """Move a node to a new position in the outline.

    Moves the node with the specified SQID to a new position. All descendants
    are moved automatically with updated paths. SQIDs are preserved.

    \b
    Examples:
        \b
        # Move node to root level at position 200
        lmk move @SQID1 --to 200

    \b
        # Move node to be child of another node
        lmk move @SQID2 --to 100-200

    \b
        # Move node before another sibling (future)
        lmk move @SQID3 --to @SQID4 --before

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Target is materialized path string
        target_mp_clean = target_mp

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = MoveNodeUseCase(filesystem=filesystem)
        use_case.execute(
            sqid=sqid_clean,
            new_mp_str=target_mp_clean,
            directory=directory,
        )

        # Output success message
        click.echo(f'Moved node @{sqid_clean} to {target_mp_clean}')
        click.echo('All files renamed successfully')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.argument('sqid')
@click.argument('new_title')
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def rename(sqid: str, new_title: str, directory: Path) -> None:
    """Rename a node with a new title.

    Updates the title in the draft file's frontmatter and renames all
    associated files to use the new slug. The SQID and materialized path
    remain unchanged.

    \b
    Examples:
        \b
        # Rename a node
        lmk rename @SQID1 "New Chapter Title"

    \b
        # Works with special characters
        lmk rename @SQID1 "Chapter 2: Hero's Journey"

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Create adapters
        filesystem = FileSystemAdapter()
        slugifier = SlugifierAdapter()

        # Execute use case
        use_case = RenameNodeUseCase(filesystem=filesystem, slugifier=slugifier)
        use_case.execute(sqid=sqid_clean, new_title=new_title, directory=directory)

        # Output success message
        click.echo(f'Renamed node @{sqid_clean} to "{new_title}"')
        click.echo('All files updated successfully')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.argument('sqid')
@click.option(
    '-r',
    '--recursive',
    is_flag=True,
    help='Delete node and all descendants recursively',
)
@click.option(
    '-p',
    '--promote',
    is_flag=True,
    help='Delete node but promote children to parent level',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def delete(sqid: str, recursive: bool, promote: bool, directory: Path) -> None:  # noqa: FBT001
    """Delete a node from the outline.

    By default, only deletes leaf nodes (nodes without children).
    Use --recursive to delete node and all descendants.
    Use --promote to delete node but promote children to parent level.

    \b
    Examples:
        \b
        # Delete a leaf node
        lmk delete @SQID1

    \b
        # Delete node and all descendants
        lmk delete @SQID1 --recursive

    \b
        # Delete node but keep children (promote to parent level)
        lmk delete @SQID1 --promote

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = DeleteNodeUseCase(filesystem=filesystem)
        deleted = use_case.execute(sqid=sqid_clean, directory=directory, recursive=recursive, promote=promote)

        # Output success message
        if recursive:
            click.echo(f'Deleted node @{sqid_clean} and {len(deleted) - 1} descendants')
        elif promote:
            click.echo(f'Deleted node @{sqid_clean} (children promoted to parent level)')
        else:
            click.echo(f'Deleted node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.argument('sqid', required=False)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def compact(sqid: str | None, directory: Path) -> None:
    """Restore clean, evenly-spaced numbering to the outline.

    Renumbers siblings at the specified level with even spacing (100s/10s/1s tier).
    If SQID provided, compacts children of that node. Otherwise compacts root level.

    \b
    Examples:
        \b
        # Compact root-level nodes
        lmk compact

    \b
        # Compact children of specific node
        lmk compact @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@') if sqid else None

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = CompactOutlineUseCase(filesystem=filesystem)
        renamed = use_case.execute(sqid=sqid_clean, directory=directory)

        # Output success message
        if sqid_clean:
            click.echo(f'Compacted {len(renamed)} children of @{sqid_clean}')
        else:
            click.echo(f'Compacted {len(renamed)} root-level nodes')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.option(
    '--repair',
    is_flag=True,
    help='Auto-repair common issues (missing files, etc.)',
)
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def doctor(repair: bool, directory: Path) -> None:  # noqa: FBT001
    """Validate outline integrity and repair common issues.

    Checks for duplicate SQIDs, missing required files, and other integrity issues.
    With --repair flag, automatically fixes common problems like missing draft/notes files.

    \b
    Examples:
        \b
        # Check outline for issues
        lmk doctor

    \b
        # Check and auto-repair issues
        lmk doctor --repair

    """
    try:
        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ValidateOutlineUseCase(filesystem=filesystem)
        result = use_case.execute(directory=directory, repair=repair)

        # Output results
        if result['valid']:
            click.echo('✓ Outline is valid')
            if result['repaired']:
                click.echo('\nRepairs performed:')
                for repair_msg in result['repaired']:
                    click.echo(f'  • {repair_msg}')
        else:
            click.echo('✗ Outline has integrity issues:', err=True)
            click.echo('', err=True)
            for violation in result['violations']:
                click.echo(f'  • {violation}', err=True)

            if not repair:  # pragma: no branch
                click.echo('', err=True)
                click.echo('Run with --repair to auto-fix common issues', err=True)

            sys.exit(1)

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


@lmk.group()
def types() -> None:
    """Manage document types for outline nodes.

    Commands for adding, removing, and listing document types associated
    with outline nodes.
    """


@types.command('list')
@click.argument('sqid')
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def types_list(sqid: str, directory: Path) -> None:
    """List all document types for a node.

    Shows all document types associated with the specified node SQID.

    \b
    Examples:
        \b
        # List types for a node
        lmk types list @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        doc_types = use_case.list_types(sqid=sqid_clean, directory=directory)

        # Output types
        if doc_types:
            click.echo(f'Document types for @{sqid_clean}:')
            for doc_type in doc_types:
                click.echo(f'  - {doc_type}')
        else:
            click.echo(f'No document types found for @{sqid_clean}', err=True)
            sys.exit(1)

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(1)  # pragma: no cover


@types.command('add')
@click.argument('doc_type')
@click.argument('sqid')
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def types_add(doc_type: str, sqid: str, directory: Path) -> None:
    """Add a new document type to a node.

    Creates a new empty file with the specified document type.
    Required types (draft, notes) cannot be added as they already exist.

    \b
    Examples:
        \b
        # Add a characters type to a node
        lmk types add characters @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        use_case.add_type(sqid=sqid_clean, doc_type=doc_type, directory=directory)

        # Output success message
        click.echo(f'Added type "{doc_type}" to node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@types.command('remove')
@click.argument('doc_type')
@click.argument('sqid')
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
def types_remove(doc_type: str, sqid: str, directory: Path) -> None:
    """Remove a document type from a node.

    Deletes the file for the specified document type.
    Required types (draft, notes) cannot be removed.

    \b
    Examples:
        \b
        # Remove a characters type from a node
        lmk types remove characters @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ManageTypesUseCase(filesystem=filesystem)
        use_case.remove_type(sqid=sqid_clean, doc_type=doc_type, directory=directory)

        # Output success message
        click.echo(f'Removed type "{doc_type}" from node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    lmk()


if __name__ == '__main__':
    main()  # pragma: no cover
