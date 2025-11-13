"""Output formatters for CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linemark.domain.entities import Node


def format_tree(nodes: list[Node], show_doctypes: bool = False, show_files: bool = False) -> str:  # noqa: FBT001, FBT002
    """Format nodes as a tree structure using Unicode box-drawing characters.

    Args:
        nodes: List of nodes sorted by materialized path
        show_doctypes: Whether to display document types (default: False)
        show_files: Whether to display file paths (default: False)

    Returns:
        Tree-formatted string with indentation and connectors

    """
    if not nodes:
        return ''

    lines: list[str] = []

    # Build tree structure
    for node in nodes:
        # Determine if this is the last sibling at each depth level
        is_last_sibling = _is_last_sibling(node, nodes)

        # Build prefix based on depth and position
        prefix = _build_prefix(node, nodes)

        # Add node line
        connector = '└── ' if is_last_sibling else '├── '
        if node.mp.depth == 1:
            # Root nodes have no prefix
            lines.append(f'{node.title} (@{node.sqid.value})')
        else:
            lines.append(f'{prefix}{connector}{node.title} (@{node.sqid.value})')

        # Add doctype metadata if requested
        if show_doctypes and node.document_types:
            doctype_str = ', '.join(sorted(node.document_types))
            # Add doctype line with proper indentation
            if node.mp.depth == 1:
                lines.append(f'└─ doctypes: {doctype_str}')
            else:
                lines.append(f'{prefix}└─ doctypes: {doctype_str}')

        # Add file metadata if requested
        if show_files and node.document_types:
            file_list = node.filenames()
            files_str = ', '.join(file_list)
            # Add files line with proper indentation
            if node.mp.depth == 1:
                lines.append(f'└─ files: {files_str}')
            else:
                lines.append(f'{prefix}└─ files: {files_str}')

    return '\n'.join(lines)


def _is_last_sibling(node: Node, all_nodes: list[Node]) -> bool:
    """Check if node is the last sibling among its peers.

    Args:
        node: Node to check
        all_nodes: All nodes in the outline

    Returns:
        True if node is the last sibling, False otherwise

    """
    # Get all siblings (nodes with same parent)
    parent_mp = node.mp.parent()
    siblings = [n for n in all_nodes if n.mp.parent() == parent_mp]

    # Check if this is the last sibling
    return node == siblings[-1] if siblings else True


def _build_prefix(node: Node, all_nodes: list[Node]) -> str:
    """Build the prefix string for a node based on its ancestors.

    Args:
        node: Node to build prefix for
        all_nodes: All nodes in the outline

    Returns:
        Prefix string with indentation and connectors

    """
    if node.mp.depth == 1:
        return ''

    parts: list[str] = []

    # Walk up the tree to build the prefix
    current_mp = node.mp.parent()
    while current_mp is not None and current_mp.depth > 1:
        # Find the node at this level
        ancestor = next((n for n in all_nodes if n.mp == current_mp), None)
        if ancestor is None:  # pragma: no cover
            break

        # Check if ancestor is last sibling
        ancestor_is_last = _is_last_sibling(ancestor, all_nodes)

        # Add connector
        if ancestor_is_last:
            parts.insert(0, '    ')
        else:
            parts.insert(0, '│   ')

        current_mp = current_mp.parent()

    return ''.join(parts)


def format_json(nodes: list[Node], show_doctypes: bool = False, show_files: bool = False) -> str:  # noqa: FBT001, FBT002
    """Format nodes as nested JSON structure.

    Args:
        nodes: List of nodes sorted by materialized path
        show_doctypes: Whether to include doctypes field (default: False)
        show_files: Whether to include files field (default: False)

    Returns:
        JSON-formatted string with nested children arrays

    """
    import json
    from typing import Any

    from linemark.domain.entities import MaterializedPath  # noqa: TC001

    def build_tree(parent_mp: MaterializedPath | None) -> list[dict[str, Any]]:
        """Recursively build tree structure."""
        result = []
        for node in nodes:
            if node.mp.parent() == parent_mp:
                node_dict: dict[str, Any] = {
                    'sqid': node.sqid.value,
                    'mp': node.mp.as_string,
                    'title': node.title,
                    'slug': node.slug,
                    'document_types': sorted(node.document_types),
                }

                # Add doctypes field if requested and available
                if show_doctypes and node.document_types:
                    node_dict['doctypes'] = sorted(node.document_types)

                # Add files field if requested and available
                if show_files and node.document_types:
                    node_dict['files'] = node.filenames()

                # Add children
                node_dict['children'] = build_tree(node.mp)

                result.append(node_dict)
        return result

    # Find the shallowest parent MP in the nodes list
    # This handles subtrees correctly (e.g., when filtering to sqid2)
    if not nodes:
        return '[]'

    # Get all unique parent MPs
    parent_mps_list = [node.mp.parent() for node in nodes]
    # Remove duplicates by comparing materialized paths
    unique_parents: list[MaterializedPath | None] = []
    for mp in parent_mps_list:
        if mp not in unique_parents:  # This works because MaterializedPath has __eq__
            unique_parents.append(mp)

    # Start from the shallowest parent (the one with smallest depth)
    # or None if we have root nodes
    root_parent = min(unique_parents, key=lambda mp: mp.depth if mp else -1)

    tree = build_tree(root_parent)
    return json.dumps(tree, indent=2)
