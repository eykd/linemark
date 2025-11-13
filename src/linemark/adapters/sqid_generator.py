"""SQID Generator adapter implementation.

Concrete implementation of SQIDGeneratorPort using the sqids library.
"""

from __future__ import annotations

from sqids import Sqids


class SQIDGeneratorAdapter:
    """Concrete SQID generator using sqids library.

    Implements SQIDGeneratorPort protocol using the sqids-python library
    for generating short, unique, URL-safe identifiers.
    """

    def __init__(self, min_length: int = 5) -> None:
        """Initialize SQID generator.

        Args:
            min_length: Minimum length of generated SQIDs (default: 5)

        """
        self._sqids = Sqids(min_length=min_length)

    def encode(self, counter: int) -> str:
        """Encode integer counter to SQID string.

        Args:
            counter: Non-negative integer (monotonically increasing)

        Returns:
            Alphanumeric SQID string

        Raises:
            ValueError: If counter is negative

        """
        if counter < 0:
            msg = f'Counter must be non-negative, got {counter}'
            raise ValueError(msg)

        return self._sqids.encode([counter])

    def decode(self, sqid: str) -> int | None:
        """Decode SQID string back to integer counter.

        Args:
            sqid: SQID string to decode

        Returns:
            Original integer counter, or None if SQID is invalid

        """
        try:
            decoded = self._sqids.decode(sqid)
            if not decoded:
                return None
            return decoded[0]
        except (ValueError, IndexError):  # pragma: no cover
            return None
