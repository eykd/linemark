"""Domain-specific exceptions for Linemark."""

from __future__ import annotations


class LinemarkError(Exception):
    """Base exception for all Linemark domain errors."""


class MaterializedPathExhaustedError(LinemarkError):
    """Raised when no more space is available for sibling insertions.

    This occurs when attempting to insert a node between two siblings
    that are consecutively numbered (e.g., 001 and 002). Solution is
    to run `lmk compact` to redistribute numbering.
    """


class DuplicateSQIDError(LinemarkError):
    """Raised when attempting to add a node with a SQID that already exists."""


class DuplicateMaterializedPathError(LinemarkError):
    """Raised when attempting to add a node with a materialized path that already exists."""


class NodeNotFoundError(LinemarkError):
    """Raised when a node cannot be found by SQID or materialized path."""


class InvalidNodeOperationError(LinemarkError):
    """Raised when attempting an invalid operation on a node.

    Examples:
    - Deleting a node with children without recursive or promote flags
    - Removing a required document type (draft or notes)
    - Moving a node to be its own descendant

    """


class FileSystemError(LinemarkError):
    """Raised when filesystem operations fail."""


class ValidationError(LinemarkError):
    """Raised when outline invariants are violated."""
