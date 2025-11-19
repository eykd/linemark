"""Command-line interface for Linemark."""

from __future__ import annotations

import sys
from pathlib import Path

import asyncclick as click

from linemark.cli.formatters import format_json, format_tree
from linemark.commanders import LinemarkCommander
from linemark.domain.exceptions import DoctypeNotFoundError, InvalidRegexError, NodeNotFoundError


@click.group()
@click.option(
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory (default: current directory)',
)
@click.pass_context
def lmk(ctx: click.Context, directory: Path) -> None:
    """Linemark - Hierarchical Markdown Outline Manager.

    A command-line tool for managing hierarchical outlines of Markdown documents
    using filename-based organization.
    """
    ctx.obj = {'directory': directory}


@lmk.command(name='agent')
@click.pass_context
def agent(ctx: click.Context) -> None:  # noqa: ARG001  # pragma: no cover
    """Start the agent."""
    from linemark.adapters.agents.s5_identity.assistant import AssistantAgent  # pragma: no cover
    from linemark.cli.tui import AgentApp  # pragma: no cover

    app = AgentApp(agent=AssistantAgent())  # pragma: no cover
    app.run()  # pragma: no cover


@lmk.command(name='compile')
@click.argument('doctype')
@click.argument('sqid', required=False)
@click.option(
    '--separator',
    default='\n\n---\n\n',
    help='Separator between documents (escape sequences interpreted)',
)
@click.pass_context
async def compile_doctype(
    ctx: click.Context,
    doctype: str,
    sqid: str | None,
    separator: str,
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
        commander = LinemarkCommander(directory=ctx.obj['directory'])
        result = await commander.compile_doctype(
            doctype=doctype,
            sqid=sqid.lstrip('@') if sqid else None,
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
@click.pass_context
async def add(
    ctx: click.Context,
    title: str,
    child_of: str | None,
    sibling_of: str | None,
    before: bool,  # noqa: FBT001
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
        commander = LinemarkCommander(directory=ctx.obj['directory'])
        node = await commander.add(
            title=title,
            child_of=child_of.lstrip('@') if child_of else None,
            sibling_of=sibling_of.lstrip('@') if sibling_of else None,
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
@click.argument('sqid', required=False, type=str)
@click.option(
    '--show-doctypes',
    is_flag=True,
    default=False,
    help='Display document types for each node',
)
@click.option(
    '--show-files',
    is_flag=True,
    default=False,
    help='Display file paths for each node',
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output in JSON format instead of tree',
)
@click.pass_context
async def list(ctx: click.Context, sqid: str | None, show_doctypes: bool, show_files: bool, output_json: bool) -> None:  # noqa: A001, FBT001
    """List all nodes in the outline, optionally filtered to a subtree.

    Displays the outline as a tree structure by default, or as nested JSON
    with --json flag.

    \b
    Examples:
        \b
        # Show full outline as tree
        lmk list

        \b
        # Show subtree starting at SQID
        lmk list @A3F7c

        \b
        # Show with document types
        lmk list --show-doctypes

        \b
        # Show subtree with doctypes as JSON
        lmk list @A3F7c --show-doctypes --json

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@') if sqid else None

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        nodes = await commander.list_nodes(sqid=sqid_clean)

        # Format and output
        if output_json:
            output = format_json(nodes, show_doctypes=show_doctypes, show_files=show_files)
        else:
            output = format_tree(nodes, show_doctypes=show_doctypes, show_files=show_files)

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
@click.pass_context
async def move(
    ctx: click.Context,
    sqid: str,
    target_mp: str,
    target_sqid_before: str | None,  # noqa: ARG001
    target_sqid_after: str | None,  # noqa: ARG001
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        await commander.move(sqid=sqid_clean, target_mp=target_mp)

        # Output success message
        click.echo(f'Moved node @{sqid_clean} to {target_mp}')
        click.echo('All files renamed successfully')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.argument('sqid')
@click.argument('new_title')
@click.pass_context
async def rename(ctx: click.Context, sqid: str, new_title: str) -> None:
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        await commander.rename(sqid=sqid_clean, new_title=new_title)

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
@click.pass_context
async def delete(ctx: click.Context, sqid: str, recursive: bool, promote: bool) -> None:  # noqa: FBT001
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        deleted_nodes = await commander.delete(sqid=sqid_clean, recursive=recursive, promote=promote)

        # Output success message
        if recursive:
            click.echo(f'Deleted node @{sqid_clean} and {len(deleted_nodes) - 1} descendants')
        elif promote:
            click.echo(f'Deleted node @{sqid_clean} (children promoted to parent level)')
        else:
            click.echo(f'Deleted node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.argument('sqid', required=False)
@click.pass_context
async def compact(ctx: click.Context, sqid: str | None) -> None:
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
        commander = LinemarkCommander(directory=ctx.obj['directory'])
        compacted_nodes = await commander.compact(sqid=sqid_clean)

        # Output success message
        if sqid_clean:
            click.echo(f'Compacted {len(compacted_nodes)} children of @{sqid_clean}')
        else:
            click.echo(f'Compacted {len(compacted_nodes)} root-level nodes')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@lmk.command()
@click.option(
    '--repair',
    is_flag=True,
    help='Auto-repair common issues (missing files, etc.)',
)
@click.pass_context
async def doctor(ctx: click.Context, repair: bool) -> None:  # noqa: FBT001
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
        commander = LinemarkCommander(directory=ctx.obj['directory'])
        result = await commander.doctor(repair=repair)

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


@lmk.command()
@click.argument('pattern')
@click.argument('subtree_sqid', required=False)
@click.option(
    '--doctype',
    'doctypes',
    multiple=True,
    help='Filter by document type (can specify multiple times)',
)
@click.option(
    '--case-sensitive',
    is_flag=True,
    help='Match case exactly (default: case-insensitive)',
)
@click.option(
    '--multiline',
    is_flag=True,
    help='Allow . to match newlines (re.DOTALL flag)',
)
@click.option(
    '--literal',
    is_flag=True,
    help='Treat pattern as literal string (escape regex)',
)
@click.option(
    '--json',
    'output_json',
    is_flag=True,
    help='Output results as JSON (one per line)',
)
@click.pass_context
async def search(
    ctx: click.Context,
    pattern: str,
    subtree_sqid: str | None,
    doctypes: tuple[str, ...],
    case_sensitive: bool,  # noqa: FBT001
    multiline: bool,  # noqa: FBT001
    literal: bool,  # noqa: FBT001
    output_json: bool,  # noqa: FBT001
) -> None:
    """Search for patterns across the outline.

    Search for regex or literal patterns across document type files,
    with optional filtering by subtree and doctype. Results are returned
    in outline order.

    \b
    Examples:

        \b
        # Search for a pattern across all files
        lmk search "TODO"

        \b
        # Search within a subtree (100-200 and descendants)
        lmk search "character" 100-200

        \b
        # Search only in notes doctypes
        lmk search "plot" --doctype notes

        \b
        # Search with multiple doctypes
        lmk search "scene" --doctype notes --doctype characters

        \b
        # Case-sensitive search
        lmk search "API" --case-sensitive

        \b
        # Multiline regex (allow . to match newlines)
        lmk search "start.*end" --multiline

        \b
        # Literal string search (escape regex)
        lmk search "[TODO]" --literal

        \b
        # Output as JSON
        lmk search "error" --json

    """
    try:
        # Strip @ prefix from subtree_sqid if provided
        if subtree_sqid:
            subtree_sqid = subtree_sqid.lstrip('@')

        # Convert doctypes tuple to list or None
        doctype_list = list(doctypes) if doctypes else None

        commander = LinemarkCommander(directory=ctx.obj['directory'])

        # Output results
        async for result in commander.search(
            pattern=pattern,
            subtree_sqid=subtree_sqid,
            doctypes=doctype_list,
            case_sensitive=case_sensitive,
            multiline=multiline,
            literal=literal,
        ):
            if output_json:
                click.echo(result.format_json())
            else:
                click.echo(result.format_plaintext())

    except InvalidRegexError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(2)  # pragma: no cover


@lmk.group()
def types() -> None:
    """Manage document types for outline nodes.

    Commands for adding, removing, and listing document types associated
    with outline nodes.
    """


@types.command('list')
@click.argument('sqid')
@click.pass_context
async def types_list(ctx: click.Context, sqid: str) -> None:
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        doc_types = await commander.list_types(sqid=sqid_clean)

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
@click.pass_context
async def types_add(ctx: click.Context, doc_type: str, sqid: str) -> None:
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        await commander.add_type(doc_type=doc_type, sqid=sqid_clean)

        # Output success message
        click.echo(f'Added type "{doc_type}" to node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@types.command('remove')
@click.argument('doc_type')
@click.argument('sqid')
@click.pass_context
async def types_remove(ctx: click.Context, doc_type: str, sqid: str) -> None:
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

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        await commander.remove_type(doc_type=doc_type, sqid=sqid_clean)

        # Output success message
        click.echo(f'Removed type "{doc_type}" from node @{sqid_clean}')

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)


@types.command('read')
@click.argument('doctype')
@click.argument('sqid')
@click.pass_context
async def types_read(ctx: click.Context, doctype: str, sqid: str) -> None:
    """Read the body content of a document type.

    Read the body of the file for the specified document type.

    \b
    Examples:

        \b
        # Read the characters type of a node
        lmk types read characters @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        body = await commander.read_type(doctype=doctype, sqid=sqid_clean)

        # Output body to stdout
        click.echo(body)

    except NodeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except DoctypeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except (OSError, PermissionError, UnicodeDecodeError, ValueError) as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(2)  # pragma: no cover


@types.command('write')
@click.argument('doctype')
@click.argument('sqid')
@click.pass_context
async def types_write(ctx: click.Context, doctype: str, sqid: str) -> None:
    """Write body content to a document type from stdin.

    Write the body content from stdin to the specified document type file,
    preserving existing YAML frontmatter. The write is atomic using a
    temporary file and rename operation.

    \b
    Examples:

        \b
        # Write content to the notes type of a node
        echo "New content" | lmk types write notes @SQID1

        \b
        # Write empty content (clear the body)
        echo -n "" | lmk types write notes @SQID1

    """
    try:
        # Strip @ prefix if provided
        sqid_clean = sqid.lstrip('@')

        # Read body content from stdin
        body = sys.stdin.read()

        commander = LinemarkCommander(directory=ctx.obj['directory'])
        await commander.write_type(doctype=doctype, sqid=sqid_clean, body=body)

    except NodeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except DoctypeNotFoundError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
    except (OSError, PermissionError, UnicodeDecodeError, ValueError) as e:  # pragma: no cover
        click.echo(f'Error: {e}', err=True)  # pragma: no cover
        sys.exit(2)  # pragma: no cover


def main() -> None:
    """Entry point for the CLI."""
    lmk()


if __name__ == '__main__':
    main()  # pragma: no cover
