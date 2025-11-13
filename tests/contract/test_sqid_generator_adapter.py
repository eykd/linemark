"""Tests for SQIDGeneratorAdapter implementation."""

from __future__ import annotations

import pytest

from linemark.adapters.sqid_generator import SQIDGeneratorAdapter
from tests.contract.test_sqid_generator_port import TestSQIDGeneratorPortContract


@pytest.fixture
def sqid_generator() -> SQIDGeneratorAdapter:
    """Provide SQIDGeneratorAdapter instance for contract tests."""
    return SQIDGeneratorAdapter()


class TestSQIDGeneratorAdapter(TestSQIDGeneratorPortContract):
    """Test SQIDGeneratorAdapter against SQIDGeneratorPort contract."""

    # Enable test collection for this subclass
    __test__ = True

    # All tests inherited from TestSQIDGeneratorPortContract
