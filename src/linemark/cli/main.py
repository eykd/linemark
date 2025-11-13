"""Command-line interface for Linemark."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from linemark.adapters.filesystem import FileSystemAdapter
from linemark.adapters.slugifier import SlugifierAdapter
from linemark.adapters.sqid_generator import SQIDGeneratorAdapter
from linemark.cli.formatters import format_json, format_tree
from linemark.use_cases.add_node import AddNodeUseCase
from linemark.use_cases.list_outline import ListOutlineUseCase
from linemark.use_cases.manage_types import ManageTypesUseCase
from linemark.use_cases.move_node import MoveNodeUseCase
from linemark.use_cases.rename_node import RenameNodeUseCase


@click.group()
def lmk() -> None:
    """Linemark - Hierarchical Markdown Outline Manager.

    A command-line tool for managing hierarchical outlines of Markdown documents
    using filename-based organization.
    """


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
    r"""Add a new outline node.

    Creates a new node with the specified TITLE. By default, adds a root-level
    node. Use --child-of to create a child node, or --sibling-of with --before
    or --after to position relative to an existing node.

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
    r"""List all nodes in the outline.

    Displays the outline as a tree structure by default, or as nested JSON
    with --json flag.

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

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


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
    r"""Move a node to a new position in the outline.

    Moves the node with the specified SQID to a new position. All descendants
    are moved automatically with updated paths. SQIDs are preserved.

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
    r"""Rename a node with a new title.

    Updates the title in the draft file's frontmatter and renames all
    associated files to use the new slug. The SQID and materialized path
    remain unchanged.

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
    r"""List all document types for a node.

    Shows all document types associated with the specified node SQID.

    Examples:
        \\b
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
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


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
    r"""Add a new document type to a node.

    Creates a new empty file with the specified document type.
    Required types (draft, notes) cannot be added as they already exist.

    Examples:
        \\b
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
    r"""Remove a document type from a node.

    Deletes the file for the specified document type.
    Required types (draft, notes) cannot be removed.

    Examples:
        \\b
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
    main()
