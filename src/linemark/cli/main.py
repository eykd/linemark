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


def main() -> None:
    """Entry point for the CLI."""
    lmk()


if __name__ == '__main__':
    main()
