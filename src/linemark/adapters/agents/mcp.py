"""Linemark MCP Server for linemark agents"""
# mypy: disable-error-code="func-returns-value"

from pathlib import Path  # pragma: no cover
from typing import Any  # pragma: no cover

from claude_agent_sdk import (  # pragma: no cover
    create_sdk_mcp_server,
    tool,
)

from linemark.commanders import CharterCommander, ConstitutionCommander  # pragma: no cover


@tool('read_constitution', 'Read the governing constitution document', {'start_path': Path})  # pragma: no cover
async def read_constitution(args: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
    """Read the governing constitution document for the given path.

    The governing constitution may reside in a parent directory of the given path, or it
    may not exist at all.

    """
    try:
        constitution_file = await ConstitutionCommander().read_constitution(args['start_path'])
    except FileNotFoundError:
        return {'content': [{'type': 'text', 'text': 'No constitution can be found.'}]}
    else:
        return {'content': [{'type': 'text', 'text': constitution_file}]}


@tool(
    'write_constitution', 'Write the governing constitution document', {'start_path': Path, 'content': str}
)  # pragma: no cover
async def write_constitution(args: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
    """Write the governing constitution document for the given path.

    The governing constitution may already exist in a parent directory of the given path,
    or it may not exist at all.

    """
    constitution_file = await ConstitutionCommander().write_constitution(args['start_path'], args['content'])
    return {'content': [{'type': 'text', 'text': f'Constitution written successfully to {constitution_file}'}]}


constitution_mcp_server = create_sdk_mcp_server(  # pragma: no cover
    name='constitution',
    version='0.1',
    tools=[
        read_constitution,
        write_constitution,
    ],
)


@tool(
    'read_charter', 'Read the story charter for the given project directory', {'start_path': Path}
)  # pragma: no cover
async def read_charter(args: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
    """Read the story charter for the given project directory."""
    charter_file = await CharterCommander().read_charter(args['start_path'])
    return {'content': [{'type': 'text', 'text': charter_file}]}


@tool(
    'write_charter', 'Write the story charter for the given project directory', {'start_path': Path, 'content': str}
)  # pragma: no cover
async def write_charter(args: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
    """Write the story charter for the given project directory."""
    charter_file = await CharterCommander().write_charter(args['start_path'], args['content'])
    return {'content': [{'type': 'text', 'text': f'Charter written successfully to {charter_file}'}]}


charter_mcp_server = create_sdk_mcp_server(  # pragma: no cover
    name='charter',
    version='0.1',
    tools=[
        read_charter,
        write_charter,
    ],
)
