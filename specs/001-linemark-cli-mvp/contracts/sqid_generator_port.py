"""SQID Generator Port Contract.

This module defines the abstract interface for generating stable, unique identifiers.
The port isolates domain logic from the specific SQID library implementation.

Constitutional Alignment:
- Hexagonal Architecture (§ I): Port defines boundary for identifier generation
- Test-First Development (§ II): Contract enables testing with predictable fake generators
"""

from typing import Protocol


class SQIDGeneratorPort(Protocol):
    """Port for SQID generation.

    This protocol defines the contract for generating short, unique, alphanumeric
    identifiers from monotonically increasing integers.

    Implementation Note:
        The sqids library (https://sqids.org/python) encodes integers into
        base-62 strings. Same integer always produces same SQID (deterministic).
    """

    def encode(self, counter: int) -> str:
        """Encode integer counter to SQID string.

        Args:
            counter: Non-negative integer (monotonically increasing)

        Returns:
            Alphanumeric SQID string (e.g., "A3F7c", "B9x2k")

        Raises:
            ValueError: If counter is negative

        Example:
            >>> generator.encode(1)
            'bM'
            >>> generator.encode(100)
            'A3F'
            >>> generator.encode(1000)
            'B9x2k'

        Note:
            Same counter value MUST always produce the same SQID (deterministic).
            This is critical for testing and reproducibility.

        """
        ...

    def decode(self, sqid: str) -> int | None:
        """Decode SQID string back to integer counter.

        Args:
            sqid: SQID string to decode

        Returns:
            Original integer counter, or None if SQID is invalid

        Example:
            >>> generator.decode('A3F')
            100
            >>> generator.decode('invalid')
            None

        Note:
            Used for deriving next counter from existing SQIDs at startup (FR-032).

        """
        ...
