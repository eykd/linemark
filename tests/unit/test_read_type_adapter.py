"""Unit tests for ReadTypeAdapter."""

from __future__ import annotations

from pathlib import Path

import anyio
import pytest

from linemark.adapters.read_type_adapter import ReadTypeAdapter
from linemark.domain.exceptions import DoctypeNotFoundError, NodeNotFoundError


@pytest.mark.asyncio
async def test_read_type_adapter_no_frontmatter(tmp_path: Path) -> None:
    """Test reading file with no frontmatter."""
    adapter = ReadTypeAdapter()

    # Create a file without frontmatter using anyio
    file_path = tmp_path / '100_ABC123_draft_test.md'
    content = 'This is just body content without frontmatter'
    await anyio.Path(file_path).write_text(content)

    # Test the private method directly (still synchronous)
    frontmatter, body = adapter._split_frontmatter_and_body(content)

    assert frontmatter == {}
    assert body == content


def test_read_type_adapter_with_frontmatter(tmp_path: Path) -> None:
    """Test reading file with frontmatter."""
    adapter = ReadTypeAdapter()

    content = """---
title: Test
---
Body content here"""

    frontmatter, body = adapter._split_frontmatter_and_body(content)

    assert frontmatter == {'title': 'Test'}
    assert body == 'Body content here'


@pytest.mark.asyncio
async def test_read_type_adapter_resolve_file_path(tmp_path: Path) -> None:
    """Test resolving file path by SQID and doctype."""
    adapter = ReadTypeAdapter()

    # Create test files using anyio
    draft_file = tmp_path / '100_ABC123_draft_test.md'
    notes_file = tmp_path / '100_ABC123_notes_test.md'
    await anyio.Path(draft_file).write_text('---\ntitle: Test\n---\nDraft')
    await anyio.Path(notes_file).write_text('---\ntitle: Test\n---\nNotes')

    # Resolve draft file
    resolved_draft = await adapter.resolve_file_path('ABC123', 'draft', tmp_path)
    assert resolved_draft == draft_file.absolute()

    # Resolve notes file
    resolved_notes = await adapter.resolve_file_path('ABC123', 'notes', tmp_path)
    assert resolved_notes == notes_file.absolute()


@pytest.mark.asyncio
async def test_read_type_adapter_node_not_found(tmp_path: Path) -> None:
    """Test error when node doesn't exist."""
    adapter = ReadTypeAdapter()

    with pytest.raises(NodeNotFoundError, match='Node @NONEXIST not found'):
        await adapter.resolve_file_path('NONEXIST', 'draft', tmp_path)


@pytest.mark.asyncio
async def test_read_type_adapter_doctype_not_found(tmp_path: Path) -> None:
    """Test error when doctype doesn't exist for node."""
    adapter = ReadTypeAdapter()

    # Create only draft file using anyio
    draft_file = tmp_path / '100_ABC123_draft_test.md'
    await anyio.Path(draft_file).write_text('---\ntitle: Test\n---\nDraft')

    # Try to access non-existent doctype
    with pytest.raises(DoctypeNotFoundError):
        await adapter.resolve_file_path('ABC123', 'nonexistent', tmp_path)
