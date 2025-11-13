"""Contract tests for CompileDoctypeUseCase.

These tests verify that CompileDoctypeUseCase follows the contract specified
in /workspace/specs/001-compile-doctype/contracts/use_case_contract.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from linemark.domain.exceptions import DoctypeNotFoundError

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort


def test_constructor_accepts_filesystem_port(filesystem_port: FileSystemPort) -> None:
    """Test T005: CompileDoctypeUseCase constructor accepts FileSystem port."""
    # Import here to ensure it fails if not implemented yet
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Act & Assert - constructor should accept filesystem port without error
    use_case = CompileDoctypeUseCase(filesystem=filesystem_port)
    assert use_case is not None
    assert hasattr(use_case, 'filesystem')


def test_execute_method_signature() -> None:
    """Test T006: CompileDoctypeUseCase.execute has correct signature."""
    import inspect

    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Act
    sig = inspect.signature(CompileDoctypeUseCase.execute)

    # Assert - verify parameter names and types
    params = sig.parameters
    assert 'self' in params
    assert 'doctype' in params
    assert 'directory' in params
    assert 'sqid' in params or 'sqid' in str(sig)  # May be positional or keyword
    assert 'separator' in params or 'separator' in str(sig)

    # Verify return type annotation
    assert sig.return_annotation is str or 'str' in str(sig.return_annotation)


def test_execute_raises_doctype_not_found_error(filesystem_port: FileSystemPort, tmp_path: Path) -> None:
    """Test T007: CompileDoctypeUseCase raises DoctypeNotFoundError when doctype doesn't exist."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange - create empty forest
    use_case = CompileDoctypeUseCase(filesystem=filesystem_port)

    # Act & Assert - should raise DoctypeNotFoundError for non-existent doctype
    with pytest.raises(DoctypeNotFoundError) as exc_info:
        use_case.execute(
            doctype='nonexistent',
            directory=tmp_path,
            sqid=None,
            separator='\n\n---\n\n',
        )

    # Verify exception message contains helpful information
    assert 'nonexistent' in str(exc_info.value)
    assert exc_info.value.doctype == 'nonexistent'


@pytest.fixture
def filesystem_port() -> FileSystemPort:
    """Provide a concrete FileSystem implementation for contract testing."""
    from linemark.adapters.filesystem import FileSystemAdapter

    return FileSystemAdapter()
