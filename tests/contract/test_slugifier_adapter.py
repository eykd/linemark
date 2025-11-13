"""Tests for SlugifierAdapter implementation."""

from __future__ import annotations

import pytest

from linemark.adapters.slugifier import SlugifierAdapter
from tests.contract.test_slugifier_port import TestSlugifierPortContract


@pytest.fixture
def slugifier() -> SlugifierAdapter:
    """Provide SlugifierAdapter instance for contract tests."""
    return SlugifierAdapter()


class TestSlugifierAdapter(TestSlugifierPortContract):
    """Test SlugifierAdapter against SlugifierPort contract."""

    # Enable test collection for this subclass
    __test__ = True

    # All tests inherited from TestSlugifierPortContract
