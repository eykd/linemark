"""Utility functions for Linemark"""

from collections.abc import Iterable
from typing import TypeVar

T = TypeVar('T')


def first[T](iterable: Iterable[T]) -> T | None:
    """Return the first element of the iterable.

    Args:
        iterable: The iterable to get the first element from.

    Returns:
        The first element of the iterable, or None if the iterable is empty.

    """
    try:
        return next(iter(iterable))
    except StopIteration:
        return None
