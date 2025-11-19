"""Tests for utility functions."""

from linemark.utils import first


def test_first_returns_first_element() -> None:
    """Test that first returns the first element of an iterable."""
    result = first([1, 2, 3])
    assert result == 1


def test_first_returns_none_for_empty_iterable() -> None:
    """Test that first returns None for an empty iterable."""
    result = first([])
    assert result is None


def test_first_works_with_generators() -> None:
    """Test that first works with generator expressions."""
    result = first(x for x in range(5))
    assert result == 0


def test_first_returns_none_for_empty_generator() -> None:
    """Test that first returns None for an empty generator."""
    result = first(x for x in range(0))
    assert result is None
