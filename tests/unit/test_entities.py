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

    def test_replace_prefix_single_level(self) -> None:
        """Replace prefix at root level."""
        from linemark.domain.entities import MaterializedPath

        # Move from 100 to 200 (root level)
        mp = MaterializedPath.from_string('100')
        new_mp = mp.replace_prefix(
            old_prefix=MaterializedPath.from_string('100'), new_prefix=MaterializedPath.from_string('200')
        )

        assert new_mp.as_string == '200'

    def test_replace_prefix_nested(self) -> None:
        """Replace prefix in nested path."""
        from linemark.domain.entities import MaterializedPath

        # Move 100-050 to 200-050 (move parent from 100 to 200)
        mp = MaterializedPath.from_string('100-050')
        new_mp = mp.replace_prefix(
            old_prefix=MaterializedPath.from_string('100'), new_prefix=MaterializedPath.from_string('200')
        )

        assert new_mp.as_string == '200-050'

    def test_replace_prefix_deep_hierarchy(self) -> None:
        """Replace prefix deep in hierarchy."""
        from linemark.domain.entities import MaterializedPath

        # Move 100-050-025-010 to 300-050-025-010
        mp = MaterializedPath.from_string('100-050-025-010')
        new_mp = mp.replace_prefix(
            old_prefix=MaterializedPath.from_string('100'), new_prefix=MaterializedPath.from_string('300')
        )

        assert new_mp.as_string == '300-050-025-010'

    def test_replace_prefix_mid_hierarchy(self) -> None:
        """Replace prefix in middle of hierarchy."""
        from linemark.domain.entities import MaterializedPath

        # Move 100-050-025 to 100-200-025 (move 100-050 to 100-200)
        mp = MaterializedPath.from_string('100-050-025')
        new_mp = mp.replace_prefix(
            old_prefix=MaterializedPath.from_string('100-050'), new_prefix=MaterializedPath.from_string('100-200')
        )

        assert new_mp.as_string == '100-200-025'

    def test_replace_prefix_no_match_raises_error(self) -> None:
        """Raise error if prefix doesn't match."""
        from linemark.domain.entities import MaterializedPath

        mp = MaterializedPath.from_string('100-050')

        with pytest.raises(ValueError, match='Path .* does not start with prefix'):
            mp.replace_prefix(
                old_prefix=MaterializedPath.from_string('200'), new_prefix=MaterializedPath.from_string('300')
            )


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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node

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
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

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
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

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
        from linemark.domain.entities import SQID, Outline

        outline = Outline()

        result = outline.get_by_sqid(SQID(value='MISSING'))

        assert result is None

    def test_get_by_mp_found(self) -> None:
        """Retrieve node by materialized path."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

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
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

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
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

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

    def test_validate_invariants_valid_outline(self) -> None:
        """Validate outline with no violations."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        node2 = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('002'),
            title='Chapter Two',
            slug='chapter-two',
        )

        outline = Outline(nodes={'A3F7c': node1, 'B8K2x': node2})

        violations = outline.validate_invariants()

        assert violations == []

    def test_validate_invariants_duplicate_sqids(self) -> None:
        """Detect duplicate SQIDs."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        node2 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('002'),
            title='Chapter Two',
            slug='chapter-two',
        )

        outline = Outline(nodes={'A3F7c': node1, 'duplicate': node2})

        violations = outline.validate_invariants()

        assert 'Duplicate SQIDs detected' in violations

    def test_validate_invariants_duplicate_mps(self) -> None:
        """Detect duplicate materialized paths."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
        )
        node2 = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter Two',
            slug='chapter-two',
        )

        outline = Outline(nodes={'A3F7c': node1, 'B8K2x': node2})

        violations = outline.validate_invariants()

        assert 'Duplicate materialized paths detected' in violations

    def test_validate_invariants_missing_required_types(self) -> None:
        """Detect missing required document types."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('001'),
            title='Chapter One',
            slug='chapter-one',
            document_types={'draft'},  # Missing 'notes'
        )

        outline = Outline(nodes={'A3F7c': node})

        violations = outline.validate_invariants()

        assert 'Node A3F7c missing required types' in violations

    def test_find_next_sibling_position_first_child(self) -> None:
        """Find position for first child (no siblings)."""
        from linemark.domain.entities import Outline

        outline = Outline()

        position = outline.find_next_sibling_position(None)

        assert position == 100

    def test_find_next_sibling_position_second_child(self) -> None:
        """Find position for second child using tier spacing."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('100'),  # First node at 100
            title='Chapter One',
            slug='chapter-one',
        )

        outline = Outline(nodes={'A3F7c': node1})

        position = outline.find_next_sibling_position(None)

        assert position == 200  # 100 + 100 (tier spacing)

    def test_find_next_sibling_position_tier_adjustment(self) -> None:
        """Test tier spacing adjusts based on sibling count."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        # Create 9 siblings (next one should use tier 10)
        nodes = {}
        for i in range(9):
            sqid_val = f'SQID{i}'
            mp_val = MaterializedPath.from_string(f'{(i + 1) * 100:03d}')
            nodes[sqid_val] = Node(
                sqid=SQID(value=sqid_val),
                mp=mp_val,
                title=f'Chapter {i + 1}',
                slug=f'chapter-{i + 1}',
            )

        outline = Outline(nodes=nodes)

        position = outline.find_next_sibling_position(None)

        assert position == 910  # 900 + 10 (tier 10 since we have 9 siblings)

    def test_find_next_sibling_position_exhausted(self) -> None:
        """Raise error when no space for new sibling."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('999'),
            title='Chapter One',
            slug='chapter-one',
        )

        outline = Outline(nodes={'A3F7c': node})

        with pytest.raises(ValueError, match='No space for new sibling'):
            outline.find_next_sibling_position(None)

    def test_add_node_to_empty_outline(self) -> None:
        """Add first node to empty outline."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        outline = Outline()
        position = outline.find_next_sibling_position(None)
        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath(segments=(position,)),
            title='Chapter One',
            slug='chapter-one',
        )

        outline.add_node(node)

        assert len(outline.nodes) == 1
        assert outline.get_by_sqid('A3F7c') == node

    def test_add_node_increments_counter(self) -> None:
        """Adding node updates next_counter."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        outline = Outline(next_counter=5)
        node = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('100'),
            title='Chapter One',
            slug='chapter-one',
        )

        outline.add_node(node)

        assert outline.next_counter == 6

    def test_add_node_duplicate_sqid_raises_error(self) -> None:
        """Adding node with duplicate SQID raises error."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('100'),
            title='Chapter One',
            slug='chapter-one',
        )
        outline = Outline(nodes={'A3F7c': node1})

        node2 = Node(
            sqid=SQID(value='A3F7c'),  # Duplicate
            mp=MaterializedPath.from_string('200'),
            title='Chapter Two',
            slug='chapter-two',
        )

        with pytest.raises(ValueError, match='SQID .* already exists'):
            outline.add_node(node2)

    def test_add_node_duplicate_mp_raises_error(self) -> None:
        """Adding node with duplicate materialized path raises error."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='A3F7c'),
            mp=MaterializedPath.from_string('100'),
            title='Chapter One',
            slug='chapter-one',
        )
        outline = Outline(nodes={'A3F7c': node1})

        node2 = Node(
            sqid=SQID(value='B8K2x'),
            mp=MaterializedPath.from_string('100'),  # Duplicate
            title='Chapter Two',
            slug='chapter-two',
        )

        with pytest.raises(ValueError, match='Materialized path .* already exists'):
            outline.add_node(node2)

    def test_move_node_to_new_parent(self) -> None:
        """Move node to new parent updates MP for node and descendants."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        # Create outline: 100 (parent1), 200 (parent2), 100-100 (child of parent1)
        parent1 = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Parent One',
            slug='parent-one',
        )
        parent2 = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('200'),
            title='Parent Two',
            slug='parent-two',
        )
        child = Node(
            sqid=SQID(value='SQID3'),
            mp=MaterializedPath.from_string('100-100'),
            title='Child',
            slug='child',
        )
        grandchild = Node(
            sqid=SQID(value='SQID4'),
            mp=MaterializedPath.from_string('100-100-100'),
            title='Grandchild',
            slug='grandchild',
        )

        outline = Outline(
            nodes={
                'SQID1': parent1,
                'SQID2': parent2,
                'SQID3': child,
                'SQID4': grandchild,
            }
        )

        # Move child from parent1 (100) to parent2 (200)
        new_mp = MaterializedPath.from_string('200-100')
        outline.move_node('SQID3', new_mp)

        # Check child MP updated
        updated_child = outline.get_by_sqid('SQID3')
        assert updated_child is not None
        assert updated_child.mp.as_string == '200-100'

        # Check grandchild MP cascaded
        updated_grandchild = outline.get_by_sqid('SQID4')
        assert updated_grandchild is not None
        assert updated_grandchild.mp.as_string == '200-100-100'

        # Check parents unchanged
        parent1_node = outline.get_by_sqid('SQID1')
        assert parent1_node is not None
        assert parent1_node.mp.as_string == '100'
        parent2_node = outline.get_by_sqid('SQID2')
        assert parent2_node is not None
        assert parent2_node.mp.as_string == '200'

    def test_move_node_to_root(self) -> None:
        """Move child node to root level."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        parent = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Parent',
            slug='parent',
        )
        child = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('100-100'),
            title='Child',
            slug='child',
        )

        outline = Outline(nodes={'SQID1': parent, 'SQID2': child})

        # Move child to root
        new_mp = MaterializedPath.from_string('200')
        outline.move_node('SQID2', new_mp)

        updated_child = outline.get_by_sqid('SQID2')
        assert updated_child is not None
        assert updated_child.mp.as_string == '200'
        assert updated_child.mp.depth == 1

    def test_move_node_with_deep_descendants(self) -> None:
        """Move node with 3+ levels of descendants."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        # Create tree: 100 -> 100-100 -> 100-100-100 -> 100-100-100-100
        nodes = {
            'SQID1': Node(sqid=SQID(value='SQID1'), mp=MaterializedPath.from_string('100'), title='L1', slug='l1'),
            'SQID2': Node(sqid=SQID(value='SQID2'), mp=MaterializedPath.from_string('100-100'), title='L2', slug='l2'),
            'SQID3': Node(
                sqid=SQID(value='SQID3'), mp=MaterializedPath.from_string('100-100-100'), title='L3', slug='l3'
            ),
            'SQID4': Node(
                sqid=SQID(value='SQID4'), mp=MaterializedPath.from_string('100-100-100-100'), title='L4', slug='l4'
            ),
        }
        outline = Outline(nodes=nodes)

        # Move L2 (100-100) to root as 300
        new_mp = MaterializedPath.from_string('300')
        outline.move_node('SQID2', new_mp)

        # Verify cascade: 300, 300-100, 300-100-100
        node2 = outline.get_by_sqid('SQID2')
        assert node2 is not None
        assert node2.mp.as_string == '300'
        node3 = outline.get_by_sqid('SQID3')
        assert node3 is not None
        assert node3.mp.as_string == '300-100'
        node4 = outline.get_by_sqid('SQID4')
        assert node4 is not None
        assert node4.mp.as_string == '300-100-100'
        node1 = outline.get_by_sqid('SQID1')
        assert node1 is not None
        assert node1.mp.as_string == '100'  # Unchanged

    def test_move_node_sqid_not_found_raises_error(self) -> None:
        """Moving non-existent node raises error."""
        from linemark.domain.entities import MaterializedPath, Outline

        outline = Outline()

        with pytest.raises(ValueError, match='Node with SQID .* not found'):
            outline.move_node('MISSING', MaterializedPath.from_string('200'))

    def test_move_node_target_position_already_exists_raises_error(self) -> None:
        """Moving to existing MP raises error."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Node One',
            slug='node-one',
        )
        node2 = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('200'),
            title='Node Two',
            slug='node-two',
        )

        outline = Outline(nodes={'SQID1': node1, 'SQID2': node2})

        # Try to move node1 to node2's position
        with pytest.raises(ValueError, match='Target path .* already occupied'):
            outline.move_node('SQID1', MaterializedPath.from_string('200'))

    def test_delete_node_leaf(self) -> None:
        """Delete leaf node with no children."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Node One',
            slug='node-one',
        )
        node2 = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('200'),
            title='Node Two',
            slug='node-two',
        )

        outline = Outline(nodes={'SQID1': node1, 'SQID2': node2})

        # Delete node1 (leaf node)
        result = outline.delete_node('SQID1')

        assert result == [node1]
        assert 'SQID1' not in outline.nodes
        assert 'SQID2' in outline.nodes

    def test_delete_node_with_children_raises_error(self) -> None:
        """Deleting node with children raises error."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        parent = Node(
            sqid=SQID(value='PARENT'),
            mp=MaterializedPath.from_string('100'),
            title='Parent',
            slug='parent',
        )
        child = Node(
            sqid=SQID(value='CHILD'),
            mp=MaterializedPath.from_string('100-100'),
            title='Child',
            slug='child',
        )

        outline = Outline(nodes={'PARENT': parent, 'CHILD': child})

        # Try to delete parent (has children)
        with pytest.raises(ValueError, match='Cannot delete node with children'):
            outline.delete_node('PARENT')

    def test_delete_node_not_found_raises_error(self) -> None:
        """Deleting non-existent node raises error."""
        from linemark.domain.entities import Outline

        outline = Outline()

        with pytest.raises(ValueError, match='Node with SQID .* not found'):
            outline.delete_node('MISSING')

    def test_delete_node_recursive(self) -> None:
        """Delete node and all descendants recursively."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        root = Node(
            sqid=SQID(value='ROOT'),
            mp=MaterializedPath.from_string('100'),
            title='Root',
            slug='root',
        )
        child1 = Node(
            sqid=SQID(value='CHILD1'),
            mp=MaterializedPath.from_string('100-100'),
            title='Child 1',
            slug='child-1',
        )
        child2 = Node(
            sqid=SQID(value='CHILD2'),
            mp=MaterializedPath.from_string('100-200'),
            title='Child 2',
            slug='child-2',
        )
        grandchild = Node(
            sqid=SQID(value='GRAND'),
            mp=MaterializedPath.from_string('100-100-100'),
            title='Grandchild',
            slug='grandchild',
        )
        sibling = Node(
            sqid=SQID(value='SIBLING'),
            mp=MaterializedPath.from_string('200'),
            title='Sibling',
            slug='sibling',
        )

        outline = Outline(
            nodes={
                'ROOT': root,
                'CHILD1': child1,
                'CHILD2': child2,
                'GRAND': grandchild,
                'SIBLING': sibling,
            }
        )

        # Delete root recursively (should delete root, child1, child2, grandchild)
        deleted = outline.delete_node_recursive('ROOT')

        assert len(deleted) == 4
        assert root in deleted
        assert child1 in deleted
        assert child2 in deleted
        assert grandchild in deleted

        # Only sibling should remain
        assert len(outline.nodes) == 1
        assert 'SIBLING' in outline.nodes

    def test_delete_node_recursive_leaf(self) -> None:
        """Deleting leaf node recursively works same as normal delete."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Node One',
            slug='node-one',
        )
        node2 = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('200'),
            title='Node Two',
            slug='node-two',
        )

        outline = Outline(nodes={'SQID1': node1, 'SQID2': node2})

        # Delete leaf recursively
        deleted = outline.delete_node_recursive('SQID1')

        assert deleted == [node1]
        assert 'SQID1' not in outline.nodes

    def test_delete_node_promote(self) -> None:
        """Delete node and promote children to parent level."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        parent = Node(
            sqid=SQID(value='PARENT'),
            mp=MaterializedPath.from_string('100'),
            title='Parent',
            slug='parent',
        )
        child1 = Node(
            sqid=SQID(value='CHILD1'),
            mp=MaterializedPath.from_string('100-100'),
            title='Child 1',
            slug='child-1',
        )
        child2 = Node(
            sqid=SQID(value='CHILD2'),
            mp=MaterializedPath.from_string('100-200'),
            title='Child 2',
            slug='child-2',
        )
        grandchild = Node(
            sqid=SQID(value='GRAND'),
            mp=MaterializedPath.from_string('100-100-100'),
            title='Grandchild',
            slug='grandchild',
        )

        outline = Outline(
            nodes={
                'PARENT': parent,
                'CHILD1': child1,
                'CHILD2': child2,
                'GRAND': grandchild,
            }
        )

        # Delete parent and promote children
        deleted, promoted = outline.delete_node_promote('PARENT')

        # Parent should be deleted
        assert deleted == [parent]
        assert 'PARENT' not in outline.nodes

        # Children promoted to root level (100 was occupied, so use next position)
        assert len(promoted) == 2
        promoted_sqids = {n.sqid.value for n in promoted}
        assert 'CHILD1' in promoted_sqids
        assert 'CHILD2' in promoted_sqids

        # Check children are now at root level (sibling to parent's former position)
        child1_new = outline.get_by_sqid('CHILD1')
        child2_new = outline.get_by_sqid('CHILD2')
        assert child1_new is not None
        assert child2_new is not None
        assert child1_new.mp.depth == 1  # Root level
        assert child2_new.mp.depth == 1  # Root level

        # Grandchild should still be child of CHILD1 (one level up)
        grandchild_new = outline.get_by_sqid('GRAND')
        assert grandchild_new is not None
        assert grandchild_new.mp.depth == 2  # Child of promoted node

    def test_delete_node_promote_leaf_node(self) -> None:
        """Promoting a leaf node works same as normal delete."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        node1 = Node(
            sqid=SQID(value='SQID1'),
            mp=MaterializedPath.from_string('100'),
            title='Node One',
            slug='node-one',
        )
        node2 = Node(
            sqid=SQID(value='SQID2'),
            mp=MaterializedPath.from_string('200'),
            title='Node Two',
            slug='node-two',
        )

        outline = Outline(nodes={'SQID1': node1, 'SQID2': node2})

        # Promote leaf node (no children to promote)
        deleted, promoted = outline.delete_node_promote('SQID1')

        assert deleted == [node1]
        assert promoted == []
        assert 'SQID1' not in outline.nodes

    def test_replace_prefix_shorter_than_old_prefix(self) -> None:
        """Test replace_prefix when path is shorter than old_prefix."""
        from linemark.domain.entities import MaterializedPath

        path = MaterializedPath.from_string('100')
        old_prefix = MaterializedPath.from_string('100-200')
        new_prefix = MaterializedPath.from_string('300')

        with pytest.raises(ValueError, match='does not start with prefix'):
            path.replace_prefix(old_prefix, new_prefix)

    def test_delete_node_recursive_nonexistent_node(self) -> None:
        """Test delete_node_recursive with nonexistent SQID raises ValueError."""
        from linemark.domain.entities import Outline

        outline = Outline()

        with pytest.raises(ValueError, match='not found'):
            outline.delete_node_recursive('NONEXISTENT')

    def test_delete_node_promote_nonexistent_node(self) -> None:
        """Test delete_node_promote with nonexistent SQID raises ValueError."""
        from linemark.domain.entities import Outline

        outline = Outline()

        with pytest.raises(ValueError, match='not found'):
            outline.delete_node_promote('NONEXISTENT')

    def test_delete_node_promote_child_to_parent_level(self) -> None:
        """Test delete_node_promote promoting children to parent's level (not root)."""
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        # Create hierarchy: root -> parent -> child1, child2
        root = Node(
            sqid=SQID(value='ROOT'),
            mp=MaterializedPath.from_string('100'),
            title='Root',
            slug='root',
        )
        parent = Node(
            sqid=SQID(value='PARENT'),
            mp=MaterializedPath.from_string('100-100'),
            title='Parent',
            slug='parent',
        )
        child1 = Node(
            sqid=SQID(value='CHILD1'),
            mp=MaterializedPath.from_string('100-100-100'),
            title='Child 1',
            slug='child-1',
        )
        child2 = Node(
            sqid=SQID(value='CHILD2'),
            mp=MaterializedPath.from_string('100-100-200'),
            title='Child 2',
            slug='child-2',
        )

        outline = Outline(
            nodes={
                'ROOT': root,
                'PARENT': parent,
                'CHILD1': child1,
                'CHILD2': child2,
            }
        )

        # Delete parent, promote children to root's level
        deleted, promoted = outline.delete_node_promote('PARENT')

        assert deleted == [parent]
        assert len(promoted) == 2

        # Children should now be at parent's level (100-XXX instead of 100-100-XXX)
        child1_new = outline.get_by_sqid('CHILD1')
        child2_new = outline.get_by_sqid('CHILD2')
        assert child1_new is not None
        assert child2_new is not None
        assert child1_new.mp.depth == 2  # Same level as parent was
        assert child2_new.mp.depth == 2
