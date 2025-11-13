"""Tests for FileSystemAdapter implementation."""

from __future__ import annotations

import pytest

from linemark.adapters.filesystem import FileSystemAdapter
from tests.contract.test_filesystem_port import TestFileSystemPortContract


@pytest.fixture
def filesystem_port() -> FileSystemAdapter:
    """Provide FileSystemAdapter instance for contract tests."""
    return FileSystemAdapter()


class TestFileSystemAdapter(TestFileSystemPortContract):
    """Test FileSystemAdapter against FileSystemPort contract."""

    # Enable test collection for this subclass
    __test__ = True

    # All tests inherited from TestFileSystemPortContract
