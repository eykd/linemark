"""Unit tests for domain entities and value objects."""

from __future__ import annotations

import pytest


class TestMaterializedPath:
    """Test suite for MaterializedPath value object."""

    def test_from_string_single_segment(self) -> None:
        """Parse single-segment path from string."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001')

        assert mp.segments == (1,)
        assert mp.as_string == '001'
        assert mp.depth == 1

    def test_from_string_multiple_segments(self) -> None:
        """Parse multi-segment path from string."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001-100-050')

        assert mp.segments == (1, 100, 50)
        assert mp.as_string == '001-100-050'
        assert mp.depth == 3

    def test_from_string_edge_cases(self) -> None:
        """Parse paths with boundary values (001, 999)."""
        from linemark.domain.entities import MaterializedPath

        mp_min = MaterializedPath.from_string('001')
        mp_max = MaterializedPath.from_string('999')

        assert mp_min.segments == (1,)
        assert mp_max.segments == (999,)

    def test_from_string_invalid_empty(self) -> None:
        """Reject empty string."""
        from linemark.domain.entities import MaterializedPath

        with pytest.raises(ValueError):
            MaterializedPath.from_string('')

    def test_from_string_invalid_format(self) -> None:
        """Reject non-numeric segments."""
        from linemark.domain.entities import MaterializedPath

        with pytest.raises(ValueError):
            MaterializedPath.from_string('abc')

    def test_from_string_out_of_range(self) -> None:
        """Reject segments outside 1-999 range."""
        from linemark.domain.entities import MaterializedPath

        with pytest.raises(ValueError):
            MaterializedPath.from_string('000')  # Too low

        with pytest.raises(ValueError):
            MaterializedPath.from_string('1000')  # Too high

    def test_parent_root_returns_none(self) -> None:
        """Root nodes (depth 1) have no parent."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001')

        assert mp.parent() is None

    def test_parent_child_returns_root(self) -> None:
        """Child node returns root as parent."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001-100')
        parent = mp.parent()

        assert parent is not None
        assert parent.segments == (1,)
        assert parent.as_string == '001'

    def test_parent_deep_hierarchy(self) -> None:
        """Parent navigation works at any depth."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001-100-050-025')
        parent = mp.parent()

        assert parent is not None
        assert parent.segments == (1, 100, 50)
        assert parent.as_string == '001-100-050'

    def test_child_creates_descendant(self) -> None:
        """Child method creates descendant at specified position."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001')
        child = mp.child(100)

        assert child.segments == (1, 100)
        assert child.as_string == '001-100'
        assert child.depth == 2

    def test_child_deep_hierarchy(self) -> None:
        """Child creation works at any depth."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('001-100')
        child = mp.child(50)

        assert child.segments == (1, 100, 50)
        assert child.as_string == '001-100-050'
        assert child.depth == 3


class TestSQID:
    """Test suite for SQID value object."""

    def test_create_valid_sqid(self) -> None:
        """Create SQID with valid alphanumeric value."""
        from linemark.domain.entities import SQID

        sqid = SQID(value='A3F7c')

        assert sqid.value == 'A3F7c'
        assert str(sqid) == 'A3F7c'

    def test_sqid_alphanumeric_validation(self) -> None:
        """Reject SQID with non-alphanumeric characters."""
        from linemark.domain.entities import SQID

        with pytest.raises(ValueError):
            SQID(value='A3F-7c')  # Contains dash

        with pytest.raises(ValueError):
            SQID(value='A3F 7c')  # Contains space

    def test_sqid_equality(self) -> None:
        """SQIDs with same value are equal."""
        from linemark.domain.entities import SQID

        sqid1 = SQID(value='A3F7c')
        sqid2 = SQID(value='A3F7c')
        sqid3 = SQID(value='B8K2x')

        assert sqid1 == sqid2
        assert sqid1 != sqid3
        assert sqid1 != 'A3F7c'  # Not equal to string

    def test_sqid_hashable(self) -> None:
        """SQIDs can be used in sets and dicts."""
        from linemark.domain.entities import SQID

        sqid1 = SQID(value='A3F7c')
        sqid2 = SQID(value='A3F7c')
        sqid3 = SQID(value='B8K2x')

        sqid_set = {sqid1, sqid2, sqid3}

        assert len(sqid_set) == 2  # sqid1 and sqid2 are duplicates
        assert sqid1 in sqid_set
        assert sqid3 in sqid_set


class TestNode:
    """Test suite for Node entity."""

    def test_create_node_with_defaults(self) -> None:
        """Create node with default document types (draft, notes)."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        mp = MaterializedPath.from_string('001')
        sqid = SQID(value='A3F7c')

        node = Node(
            sqid=sqid,
            mp=mp,
            title='Chapter One',
            slug='chapter-one',
        )

        assert node.sqid == sqid
        assert node.mp == mp
        assert node.title == 'Chapter One'
        assert node.slug == 'chapter-one'
        assert node.document_types == {'draft', 'notes'}

    def test_create_node_with_custom_types(self) -> None:
        """Create node with additional document types."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        mp = MaterializedPath.from_string('001-100')
        sqid = SQID(value='B8K2x')

        node = Node(
            sqid=sqid,
            mp=mp,
            title='Section Two',
            slug='section-two',
            document_types={'draft', 'notes', 'characters', 'locations'},
        )

        assert node.document_types == {'draft', 'notes', 'characters', 'locations'}

    def test_filename_generation(self) -> None:
        """Generate filename for specific document type."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001-100'),
            title='Chapter One',
            slug='chapter-one',
        )

        filename = node.filename('draft')

        assert filename == '001-100_A3F7c_draft_chapter-one.md'

    def test_filenames_returns_all(self) -> None:
        """Get all filenames for node."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
            document_types={'draft', 'notes', 'characters'},
        )

        filenames = node.filenames()

        # Should be sorted alphabetically by type
        assert filenames == [
            '001_A3F7c_characters_chapter-one.md',
            '001_A3F7c_draft_chapter-one.md',
            '001_A3F7c_notes_chapter-one.md',
        ]

    def test_validate_required_types_success(self) -> None:
        """Validation passes when draft and notes present."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
            document_types={'draft', 'notes', 'custom'},
        )

        assert node.validate_required_types() is True

    def test_validate_required_types_failure(self) -> None:
        """Validation fails when required types missing."""
        from linemark.domain.entities import MaterializedPath, Node, SQID

        node_no_draft = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
            document_types={'notes'},  # Missing draft
        )

        node_no_notes = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('002'),
            title='Chapter Two',
            slug='chapter-two',
            document_types={'draft'},  # Missing notes
        )

        assert node_no_draft.validate_required_types() is False
        assert node_no_notes.validate_required_types() is False


class TestOutline:
    """Test suite for Outline aggregate root."""

    def test_create_empty_outline(self) -> None:
        """Create outline with no nodes."""
        from linemark.domain.entities import Outline

        outline = Outline()

        assert outline.nodes == {}
        assert outline.next_counter == 1

    def test_create_outline_with_nodes(self) -> None:
        """Create outline with initial nodes."""
        from linemark.domain.entities import MaterializedPath, Node, Outline, SQID

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )

        outline = Outline(
            nodes={'A3F7c': node1},
            next_counter=2,
        )

        assert len(outline.nodes) == 1
        assert outline.next_counter == 2

    def test_get_by_sqid_found(self) -> None:
        """Retrieve node by SQID value."""
        from linemark.domain.entities import MaterializedPath, Node, Outline, SQID

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        outline = Outline(nodes={'A3F7c': node})

        # Test with SQID object
        result1 = outline.get_by_sqid(SQID(value='A3F7c'))
        assert result1 == node

        # Test with string
        result2 = outline.get_by_sqid('A3F7c')
        assert result2 == node

    def test_get_by_sqid_not_found(self) -> None:
        """Return None when SQID not found."""
        from linemark.domain.entities import Outline, SQID

        outline = Outline()

        result = outline.get_by_sqid(SQID(value='MISSING'))

        assert result is None

    def test_get_by_mp_found(self) -> None:
        """Retrieve node by materialized path."""
        from linemark.domain.entities import MaterializedPath, Node, Outline, SQID

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001-100'),
            title='Chapter One',
            slug='chapter-one',
        )
        outline = Outline(nodes={'A3F7c': node})

        # Test with MaterializedPath object
        result1 = outline.get_by_mp(MaterializedPath.from_string('001-100'))
        assert result1 == node

        # Test with string
        result2 = outline.get_by_mp('001-100')
        assert result2 == node

    def test_get_by_mp_not_found(self) -> None:
        """Return None when materialized path not found."""
        from linemark.domain.entities import MaterializedPath, Outline

        outline = Outline()

        result = outline.get_by_mp(MaterializedPath.from_string('999'))

        assert result is None

    def test_all_sorted(self) -> None:
        """Get all nodes sorted by materialized path."""
        from linemark.domain.entities import MaterializedPath, Node, Outline, SQID

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        node2 = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('001-100'),
            title='Section One',
            slug='section-one',
        )
        node3 = Node(
            sqid=SQID(value='C2N9y'),
            mp=MaterializedPath.from_string('002'),
            title='Chapter Two',
            slug='chapter-two',
        )

        outline = Outline(nodes={'A3F7c': node1, 'C2N9y': node3, 'B8K2x': node2})

        sorted_nodes = outline.all_sorted()

        assert len(sorted_nodes) == 3
        assert sorted_nodes[0].mp.as_string == '001'
        assert sorted_nodes[1].mp.as_string == '001-100'
        assert sorted_nodes[2].mp.as_string == '002'

    def test_root_nodes(self) -> None:
        """Get root-level nodes (depth 1)."""
        from linemark.domain.entities import MaterializedPath, Node, Outline, SQID

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        node2 = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('001-100'),
            title='Section One',
            slug='section-one',
        )
        node3 = Node(
            sqid=SQID(value='C2N9y'),
            mp=MaterializedPath.from_string('002'),
            title='Chapter Two',
            slug='chapter-two',
        )

        outline = Outline(nodes={'A3F7c': node1, 'B8K2x': node2, 'C2N9y': node3})

        roots = outline.root_nodes()

        assert len(roots) == 2
        assert node1 in roots
        assert node3 in roots
        assert node2 not in roots
