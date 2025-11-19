"""Test configuration and fixtures."""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

# Monkey patch pytest_textual_snapshot to fix Path issue with newer pytest versions
try:
    import pytest_textual_snapshot

    def patched_node_to_report_path(node: pytest.Item) -> Path:
        """Generate a report file name for a test node (patched for pytest compatibility)."""
        from pytest_textual_snapshot import get_tempdir

        tempdir = get_tempdir()
        path_info, _, name = node.reportinfo()
        # Convert string to Path if needed (fixes compatibility with pytest >= 8.0)
        if isinstance(path_info, str):
            path: Path = Path(path_info)
        elif isinstance(path_info, PathLike):
            path = Path(path_info)
        else:
            path = path_info
        temp = Path(path.parent)
        base: list[str] = []
        while temp != temp.parent and temp.name != 'tests':
            base.append(temp.name)
            temp = temp.parent
        parts: list[str] = []
        if base:
            parts.append('_'.join(reversed(base)))
        parts.extend((path.name.replace('.', '_'), name.replace('[', '_').replace(']', '_')))
        return Path(tempdir.name) / '_'.join(parts)

    pytest_textual_snapshot.node_to_report_path = patched_node_to_report_path
except ImportError:
    # pytest-textual-snapshot not installed
    pass


def invoke_asyncclick_command(args: list[str], stdin_content: str | None = None) -> tuple[int, str, str]:
    """Invoke an asyncclick command synchronously for testing.

    This helper properly runs asyncclick commands in tests by setting sys.argv
    and running the event loop to completion, capturing stdout and stderr.

    Args:
        args: Command-line arguments including the program name
        stdin_content: Optional stdin input to provide to the command

    Returns:
        Tuple of (exit_code, stdout, stderr)

    Example:
        exit_code, stdout, stderr = invoke_asyncclick_command(['lmk', '--directory', '/tmp', 'add', 'Test'])
        exit_code, stdout, stderr = invoke_asyncclick_command(['lmk', 'types', 'write', 'draft', '@ABC'], stdin_content='content')

    """
    import asyncio
    import sys
    from io import StringIO

    from linemark.cli.main import lmk

    # Set sys.argv for the command
    original_argv = sys.argv
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    original_stdin = sys.stdin

    stdout_capture = StringIO()
    stderr_capture = StringIO()
    stdin_input = StringIO(stdin_content) if stdin_content is not None else None
    exit_code = [0]  # Use list to allow mutation in nested function

    try:
        sys.argv = args
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        if stdin_input is not None:
            sys.stdin = stdin_input

        async def run_command() -> int:
            result = lmk.main(standalone_mode=False, prog_name=args[0])
            if asyncio.iscoroutine(result):
                code = await result
            else:
                code = result
            return code if isinstance(code, int) else 0

        # Run the async command
        try:
            exit_code[0] = asyncio.run(run_command())
        except SystemExit as e:
            exit_code[0] = e.code if isinstance(e.code, int) else 0
    finally:
        sys.argv = original_argv
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        sys.stdin = original_stdin

    return exit_code[0], stdout_capture.getvalue(), stderr_capture.getvalue()
