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
