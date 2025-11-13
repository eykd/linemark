"""Contract tests for SQIDGeneratorPort implementations.

These tests verify that any concrete implementation of SQIDGeneratorPort
follows the protocol contract correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from linemark.ports.sqid_generator import SQIDGeneratorPort


class TestSQIDGeneratorPortContract:
    """Contract tests for SQIDGeneratorPort protocol.

    To test an implementation, create a test class that inherits from this
    and provides a sqid_generator fixture.
    """

    # Mark as non-collection to avoid pytest discovering this base class
    __test__ = False

    def test_encode_positive_integers(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encode positive integers to SQID strings."""
        sqid1 = sqid_generator.encode(1)
        sqid100 = sqid_generator.encode(100)
        sqid1000 = sqid_generator.encode(1000)

        assert isinstance(sqid1, str)
        assert isinstance(sqid100, str)
        assert isinstance(sqid1000, str)
        assert len(sqid1) > 0
        assert len(sqid100) > 0
        assert len(sqid1000) > 0

    def test_encode_is_deterministic(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Same counter always produces same SQID."""
        sqid1_first = sqid_generator.encode(42)
        sqid1_second = sqid_generator.encode(42)

        assert sqid1_first == sqid1_second

    def test_encode_produces_alphanumeric_only(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encoded SQID contains only alphanumeric characters."""
        sqid = sqid_generator.encode(123)

        assert sqid.isalnum()

    def test_encode_different_counters_produce_different_sqids(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Different counters produce different SQIDs."""
        sqid1 = sqid_generator.encode(1)
        sqid2 = sqid_generator.encode(2)
        sqid100 = sqid_generator.encode(100)

        assert sqid1 != sqid2
        assert sqid1 != sqid100
        assert sqid2 != sqid100

    def test_encode_negative_counter_raises_error(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encoding negative counter raises ValueError."""
        with pytest.raises(ValueError):
            sqid_generator.encode(-1)

    def test_encode_zero_succeeds(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encoding zero counter succeeds."""
        sqid = sqid_generator.encode(0)

        assert isinstance(sqid, str)
        assert len(sqid) > 0
        assert sqid.isalnum()

    def test_decode_valid_sqid_returns_counter(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Decode valid SQID returns original counter."""
        original_counter = 42
        sqid = sqid_generator.encode(original_counter)

        decoded = sqid_generator.decode(sqid)

        assert decoded == original_counter

    def test_decode_invalid_sqid_returns_none(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Decode invalid SQID returns None."""
        invalid_sqids = ['!!!invalid!!!', 'not-a-sqid', '', '   ']

        for invalid in invalid_sqids:
            result = sqid_generator.decode(invalid)
            assert result is None, f'Expected None for invalid SQID: {invalid!r}'

    def test_encode_decode_round_trip(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encoding then decoding returns original value."""
        counters = [0, 1, 10, 100, 1000, 9999]

        for counter in counters:
            sqid = sqid_generator.encode(counter)
            decoded = sqid_generator.decode(sqid)

            assert decoded == counter, f'Round trip failed for counter {counter}'

    def test_encode_large_counters(self, sqid_generator: SQIDGeneratorPort) -> None:
        """Encode large counter values."""
        large_counter = 1_000_000
        sqid = sqid_generator.encode(large_counter)

        assert isinstance(sqid, str)
        assert len(sqid) > 0
        assert sqid.isalnum()

        decoded = sqid_generator.decode(sqid)
        assert decoded == large_counter
