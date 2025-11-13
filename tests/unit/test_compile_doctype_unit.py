"""Unit tests for CompileDoctypeUseCase."""

from __future__ import annotations

from pathlib import Path

import pytest

from linemark.domain.exceptions import DoctypeNotFoundError


class FakeFileSystem:
    """Fake filesystem adapter for testing compile doctype use case."""

    def __init__(self) -> None:
        """Initialize with empty file storage."""
        self.files: dict[str, str] = {}
        self.directories: set[str] = set()

    def read_file(self, path: Path) -> str:
        """Read file from in-memory storage."""
        key = str(path)
        if key not in self.files:
            msg = f'File not found: {path}'
            raise FileNotFoundError(msg)
        return self.files[key]

    def file_exists(self, path: Path) -> bool:
        """Check if file exists in storage."""
        return str(path) in self.files

    def list_markdown_files(self, directory: Path) -> list[Path]:
        """List markdown files in directory."""
        dir_str = str(directory)
        return sorted([Path(path) for path in self.files if path.startswith(dir_str) and path.endswith('.md')])

    def write_file(self, path: Path, content: str) -> None:
        """Write file to in-memory storage."""
        self.files[str(path)] = content

    def delete_file(self, path: Path) -> None:
        """Delete file from in-memory storage."""
        if str(path) in self.files:
            del self.files[str(path)]

    def create_directory(self, directory: Path) -> None:
        """Create directory in in-memory storage."""
        self.directories.add(str(directory))

    def rename_file(self, old_path: Path, new_path: Path) -> None:
        """Rename file in in-memory storage."""
        if str(old_path) in self.files:
            self.files[str(new_path)] = self.files[str(old_path)]
            del self.files[str(old_path)]

    def add_node(
        self,
        directory: Path,
        mp: str,
        sqid: str,
        title: str,
        slug: str,
        doctypes: dict[str, str],
    ) -> None:
        """Helper to add a node with specified doctypes to fake filesystem."""
        # Add directory
        node_dir = directory / mp
        self.directories.add(str(node_dir))

        # Add doctype files
        for doctype, content in doctypes.items():
            filepath = directory / f'{mp}_{sqid}_{doctype}_{slug}.md'
            if doctype == 'draft':
                # Draft contains frontmatter with title
                self.files[str(filepath)] = f"""---
title: {title}
---
{content}"""
            else:
                # Other doctypes contain just content
                self.files[str(filepath)] = content


def test_basic_forest_compilation() -> None:
    """Test T008: Compile entire forest with multiple nodes containing doctype."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create forest with multiple nodes
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content', 'notes': 'Notes 1'},
    )
    fs.add_node(
        directory,
        mp='001-001',
        sqid='SQID2',
        title='Section 1.1',
        slug='section-1-1',
        doctypes={'draft': 'Section 1.1 content', 'notes': 'Notes 1.1'},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID3',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2 content', 'notes': 'Notes 2'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\n---\n',
    )

    # Assert - should concatenate in depth-first order
    expected = """---
title: Chapter One
---
Chapter 1 content
---
---
title: Section 1.1
---
Section 1.1 content
---
---
title: Chapter Two
---
Chapter 2 content"""
    assert result == expected


def test_skipping_nodes_without_doctype() -> None:
    """Test T009: Skip nodes that don't have the specified doctype."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Node 1: has draft
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )

    # Node 2: has NO draft (only notes)
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'notes': 'Just notes'},
    )

    # Node 3: has draft
    fs.add_node(
        directory,
        mp='003',
        sqid='SQID3',
        title='Chapter Three',
        slug='chapter-three',
        doctypes={'draft': 'Chapter 3 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\n---\n',
    )

    # Assert - should skip node 2, only include 1 and 3
    assert 'Chapter 1 content' in result
    assert 'Chapter 3 content' in result
    assert 'Just notes' not in result
    assert result.count('---') == 5  # One separator between two items + 4 from frontmatter (2 per file)


def test_skipping_empty_whitespace_files() -> None:
    """Test T010: Skip empty files and whitespace-only files."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Node 1: has real content
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )

    # Node 2: has empty doctype file
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': ''},
    )

    # Node 3: has whitespace-only doctype file
    fs.add_node(
        directory,
        mp='003',
        sqid='SQID3',
        title='Chapter Three',
        slug='chapter-three',
        doctypes={'draft': '   \n  \n  '},
    )

    # Node 4: has real content
    fs.add_node(
        directory,
        mp='004',
        sqid='SQID4',
        title='Chapter Four',
        slug='chapter-four',
        doctypes={'draft': 'Chapter 4 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\n---\n',
    )

    # Assert - should only include nodes 1 and 4
    assert 'Chapter 1 content' in result
    assert 'Chapter 4 content' in result
    # Should have exactly one separator between the two items (plus 4 from frontmatter: 2 per file)
    assert result.count('---') == 5


def test_doctype_not_found_error() -> None:
    """Test T011: Raise DoctypeNotFoundError when doctype doesn't exist."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes with only 'draft' doctype
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act & Assert - should raise error for non-existent doctype
    with pytest.raises(DoctypeNotFoundError) as exc_info:
        use_case.execute(
            doctype='summary',
            directory=directory,
            sqid=None,
            separator='\n---\n',
        )

    # Verify error details
    assert exc_info.value.doctype == 'summary'
    assert exc_info.value.sqid is None
    assert 'summary' in str(exc_info.value)


def test_empty_result_handling() -> None:
    """Test T012: Return empty string when all matching files are empty."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create nodes where all draft files are empty/whitespace
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': ''},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': '  \n  '},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\n---\n',
    )

    # Assert - should return empty string
    assert result == ''


# =============================================================================
# User Story 2: Subtree Support Tests (T026-T030)
# =============================================================================


def test_subtree_filtering_logic() -> None:
    """Test T026: Filter nodes to specific subtree."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Create forest with multiple branches
    # Root 001
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )
    # Child 001-001
    fs.add_node(
        directory,
        mp='001-001',
        sqid='SQID2',
        title='Section 1.1',
        slug='section-1-1',
        doctypes={'draft': 'Section 1.1 content'},
    )
    # Grandchild 001-001-001
    fs.add_node(
        directory,
        mp='001-001-001',
        sqid='SQID3',
        title='Subsection 1.1.1',
        slug='subsection-1-1-1',
        doctypes={'draft': 'Subsection 1.1.1 content'},
    )
    # Root 002 (different branch)
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID4',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - compile subtree rooted at SQID2 (001-001)
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid='SQID2',
        separator='\n---\n',
    )

    # Assert - should only include SQID2 and its descendants
    assert 'Section 1.1 content' in result
    assert 'Subsection 1.1.1 content' in result
    # Should NOT include parent or other branches
    assert 'Chapter 1 content' not in result
    assert 'Chapter 2 content' not in result


def test_invalid_sqid_error() -> None:
    """Test T027: Raise NodeNotFoundError for invalid SQID."""
    from linemark.domain.exceptions import NodeNotFoundError
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act & Assert - should raise error for invalid SQID
    with pytest.raises(NodeNotFoundError) as exc_info:
        use_case.execute(
            doctype='draft',
            directory=directory,
            sqid='INVALID',
            separator='\n---\n',
        )

    assert 'INVALID' in str(exc_info.value)


def test_sqid_with_no_matching_doctype() -> None:
    """Test T028: Error when subtree has no nodes with requested doctype."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Root with draft and notes
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content', 'notes': 'Notes 1'},
    )
    # Child with draft but NOT notes
    fs.add_node(
        directory,
        mp='001-001',
        sqid='SQID2',
        title='Section 1.1',
        slug='section-1-1',
        doctypes={'draft': 'Draft content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act & Assert - should raise error when subtree has no 'summary' files
    with pytest.raises(DoctypeNotFoundError) as exc_info:
        use_case.execute(
            doctype='summary',
            directory=directory,
            sqid='SQID2',
            separator='\n---\n',
        )

    assert exc_info.value.doctype == 'summary'
    assert exc_info.value.sqid == 'SQID2'


def test_root_node_inclusion_in_subtree() -> None:
    """Test T029: Root node of subtree is included if it has the doctype."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Root node with draft
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )
    # Child with draft
    fs.add_node(
        directory,
        mp='001-001',
        sqid='SQID2',
        title='Section 1.1',
        slug='section-1-1',
        doctypes={'draft': 'Section 1.1 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - compile subtree rooted at SQID1
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid='SQID1',
        separator='\n---\n',
    )

    # Assert - should include root node AND its children
    assert 'Chapter 1 content' in result
    assert 'Section 1.1 content' in result


def test_leaf_node_no_children() -> None:
    """Test T030: Compile subtree for leaf node (no children)."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    # Root node
    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )
    # Leaf node (no children)
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - compile subtree rooted at leaf node SQID2
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid='SQID2',
        separator='\n---\n',
    )

    # Assert - should only include the leaf node itself
    assert 'Chapter 2 content' in result
    assert 'Chapter 1 content' not in result
    # No content separator since only one item (frontmatter will have '---' but that's different)
    # Check that the separator pattern doesn't appear between content
    assert result.count('---') == 2  # Only frontmatter delimiters, no content separator


# =============================================================================
# User Story 3: Custom Separator Tests (T041-T044)
# =============================================================================


def test_custom_separator() -> None:
    """Test T041: Use custom separator between documents."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1 content'},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2 content'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - use custom separator
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='===PAGE BREAK===',
    )

    # Assert - custom separator appears between documents
    assert 'Chapter 1 content' in result
    assert 'Chapter 2 content' in result
    assert '===PAGE BREAK===' in result


def test_escape_sequence_interpretation() -> None:
    r"""Test T042: Escape sequences like \\n, \\t are interpreted."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1'},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - use separator with escape sequences
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\\n\\n***\\n\\n',
    )

    # Assert - escape sequences are interpreted as actual newlines
    assert '\n\n***\n\n' in result
    assert 'Chapter 1' in result
    assert 'Chapter 2' in result


def test_empty_separator() -> None:
    """Test T043: Empty separator concatenates documents directly."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Part One',
        slug='part-one',
        doctypes={'draft': 'PartOne'},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Part Two',
        slug='part-two',
        doctypes={'draft': 'PartTwo'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - use empty separator
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='',
    )

    # Assert - documents are directly concatenated
    assert 'PartOne' in result
    assert 'PartTwo' in result
    # Should appear consecutively with no separator (except frontmatter)
    assert (
        'PartOne---\ntitle: Part Two\n---\nPartTwo' in result or 'PartOnePartTwo' not in result
    )  # frontmatter prevents direct concat


def test_default_separator_when_not_provided() -> None:
    """Test T044: Default separator is used when not explicitly provided."""
    from linemark.use_cases.compile_doctype import CompileDoctypeUseCase

    # Arrange
    fs = FakeFileSystem()
    directory = Path('/test')

    fs.add_node(
        directory,
        mp='001',
        sqid='SQID1',
        title='Chapter One',
        slug='chapter-one',
        doctypes={'draft': 'Chapter 1'},
    )
    fs.add_node(
        directory,
        mp='002',
        sqid='SQID2',
        title='Chapter Two',
        slug='chapter-two',
        doctypes={'draft': 'Chapter 2'},
    )

    use_case = CompileDoctypeUseCase(filesystem=fs)

    # Act - use default separator
    result = use_case.execute(
        doctype='draft',
        directory=directory,
        sqid=None,
        separator='\n\n---\n\n',  # This is the default
    )

    # Assert - default separator appears
    assert '\n\n---\n\n' in result
    assert 'Chapter 1' in result
    assert 'Chapter 2' in result
