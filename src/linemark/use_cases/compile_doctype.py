"""Compile doctype use case.

This module implements the use case for compiling all doctype files
from a forest or subtree into a single concatenated document.
"""

from __future__ import annotations

import codecs
import re
from typing import TYPE_CHECKING

from linemark.domain.entities import SQID, MaterializedPath, Node
from linemark.domain.exceptions import DoctypeNotFoundError, NodeNotFoundError

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.ports.filesystem import FileSystemPort

# Filename pattern per FR-030: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$',
)


class CompileDoctypeUseCase:
    """Use case for compiling doctype files into a single document.

    Orchestrates the compilation of all doctype files from a forest or subtree,
    producing a single concatenated output with configurable separators.
    """

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize use case with filesystem port.

        Args:
            filesystem: Port for file system operations

        """
        self.filesystem = filesystem

    def _extract_title_from_frontmatter(self, content: str) -> str:  # noqa: PLR6301
        """Extract title from YAML frontmatter.

        Args:
            content: File content with YAML frontmatter

        Returns:
            Title string from frontmatter, or 'Untitled' if not found

        """
        if not content.startswith('---\n'):
            return 'Untitled'  # pragma: no cover

        parts = content.split('---\n', 2)
        if len(parts) < 3:  # noqa: PLR2004
            return 'Untitled'  # pragma: no cover

        frontmatter = parts[1]
        for line in frontmatter.split('\n'):
            if line.startswith('title:'):  # pragma: no branch
                return line.split('title:', 1)[1].strip()

        return 'Untitled'  # pragma: no cover

    def _list_nodes(self, directory: Path) -> list[Node]:
        """List all nodes in the forest.

        Args:
            directory: Working directory containing the forest

        Returns:
            List of nodes sorted by materialized path

        """
        nodes_by_sqid: dict[str, Node] = {}

        # List all markdown files
        md_files = self.filesystem.list_markdown_files(directory)

        # Parse each file
        for file_path in md_files:
            match = FILENAME_PATTERN.match(file_path.name)
            if not match:
                continue  # pragma: no cover

            mp_str = match.group('mp')
            sqid_str = match.group('sqid')
            doc_type = match.group('type')
            slug = match.group('slug') or ''

            # Get or create node for this SQID
            if sqid_str not in nodes_by_sqid:
                # For compilation, we need title from draft file
                if doc_type == 'draft':
                    content = self.filesystem.read_file(file_path)
                    title = self._extract_title_from_frontmatter(content)
                else:
                    # Skip non-draft files if node doesn't exist yet
                    continue

                # Create new node
                node = Node(
                    sqid=SQID(value=sqid_str),
                    mp=MaterializedPath.from_string(mp_str),
                    title=title,
                    slug=slug or 'untitled',
                    document_types=set(),
                )
                nodes_by_sqid[sqid_str] = node

            # Add document type
            nodes_by_sqid[sqid_str].document_types.add(doc_type)

        # Return nodes sorted by materialized path
        return sorted(nodes_by_sqid.values(), key=lambda n: n.mp.as_string)

    def _filter_subtree(self, nodes: list[Node], sqid: str) -> list[Node]:  # noqa: PLR6301
        """Filter nodes to only include subtree rooted at given SQID.

        Args:
            nodes: All nodes in the forest
            sqid: SQID of subtree root

        Returns:
            Nodes in the subtree (root + descendants)

        Raises:
            NodeNotFoundError: If SQID doesn't exist in forest

        """
        # Find the root node
        root_node = None
        for node in nodes:
            if node.sqid.value == sqid:
                root_node = node
                break

        if root_node is None:
            msg = f"Node with SQID '{sqid}' not found"
            raise NodeNotFoundError(msg)

        # Filter to subtree (node + descendants)
        root_mp = root_node.mp.as_string
        subtree_nodes = []

        for node in nodes:
            node_mp = node.mp.as_string
            # Include if it's the root OR starts with root's MP followed by a dash
            if node_mp == root_mp or node_mp.startswith(f'{root_mp}-'):
                subtree_nodes.append(node)

        return subtree_nodes

    def _validate_doctype_exists(self, nodes: list[Node], doctype: str, sqid: str | None) -> None:  # noqa: PLR6301
        """Validate that doctype exists in at least one node.

        Args:
            nodes: Nodes to check
            doctype: Doctype to validate
            sqid: Optional SQID for error message context

        Raises:
            DoctypeNotFoundError: If doctype doesn't exist in any node

        """
        for node in nodes:
            if doctype in node.document_types:
                return  # Found at least one

        # Not found - raise error
        raise DoctypeNotFoundError(doctype=doctype, sqid=sqid)

    def _is_empty_content(self, content: str) -> bool:  # noqa: PLR6301
        """Check if content is empty or whitespace-only.

        This method checks the actual content after frontmatter.
        Frontmatter itself doesn't count as content.

        Args:
            content: File content to check (may include frontmatter)

        Returns:
            True if content is empty or only whitespace

        """
        if not content:
            return True  # pragma: no cover

        # Strip frontmatter if present
        if content.startswith('---\n'):
            parts = content.split('---\n', 2)
            if len(parts) >= 3:  # noqa: PLR2004
                # Get content after frontmatter
                actual_content = parts[2]
                return not actual_content or actual_content.isspace()

        # No frontmatter - check content directly
        return content.isspace()  # pragma: no cover

    def _get_doctype_filepath(self, directory: Path, node: Node, doctype: str) -> Path:  # noqa: PLR6301
        """Build filepath for a node's doctype file.

        Args:
            directory: Working directory
            node: Node to get file for
            doctype: Doctype name

        Returns:
            Path to the doctype file

        """
        # Pattern: <mp>_<sqid>_<type>_<slug>.md
        filename = f'{node.mp.as_string}_{node.sqid.value}_{doctype}_{node.slug}.md'
        return directory / filename

    def _process_separator(self, separator: str) -> str:  # noqa: PLR6301
        r"""Process separator to interpret escape sequences.

        Args:
            separator: Separator string (may contain escape sequences like \\n, \\t)

        Returns:
            Processed separator with escape sequences interpreted

        """
        # Use codecs.decode to interpret escape sequences
        try:
            return codecs.decode(separator, 'unicode_escape')
        except Exception:  # noqa: BLE001  # pragma: no cover
            # If decode fails, return as-is (defensive programming)
            return separator

    def execute(
        self,
        doctype: str,
        directory: Path,
        sqid: str | None = None,
        separator: str = '\n\n---\n\n',
    ) -> str:
        """Compile all doctype files into single output.

        Args:
            doctype: Name of doctype to compile (e.g., 'draft', 'notes')
            directory: Working directory containing the forest
            sqid: Optional SQID to limit to subtree (None = entire forest)
            separator: Separator between documents (escape sequences interpreted)

        Returns:
            Compiled content as string (empty string if no content found)

        Raises:
            DoctypeNotFoundError: If doctype doesn't exist in compilation scope
            NodeNotFoundError: If sqid provided but node doesn't exist
            FileSystemError: If file system operations fail

        """
        # 1. Get all nodes
        all_nodes = self._list_nodes(directory)

        # 2. Filter to subtree if SQID provided
        nodes = self._filter_subtree(all_nodes, sqid) if sqid is not None else all_nodes

        # 3. Validate doctype exists
        self._validate_doctype_exists(nodes, doctype, sqid)

        # 4. Process separator (interpret escape sequences)
        processed_separator = self._process_separator(separator)

        # 5. Collect content from matching nodes
        contents: list[str] = []

        for node in nodes:
            # Check if node has this doctype
            if doctype not in node.document_types:
                continue  # pragma: no cover

            # Get filepath for this doctype
            filepath = self._get_doctype_filepath(directory, node, doctype)

            # Read file content
            try:
                content = self.filesystem.read_file(filepath)
            except FileNotFoundError:  # pragma: no cover
                # File doesn't exist - skip # pragma: no cover
                continue  # pragma: no cover

            # Skip if empty or whitespace-only
            if self._is_empty_content(content):
                continue

            # Add to collection
            contents.append(content)

        # 6. Concatenate with separator
        if not contents:
            return ''

        return processed_separator.join(contents)
