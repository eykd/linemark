"""Use case for validating and repairing outline integrity."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, TypedDict

import yaml

if TYPE_CHECKING:
    from pathlib import Path

    from linemark.domain.entities import Outline
    from linemark.ports.filesystem import FileSystemPort

# Pattern for parsing filenames: <mp>_<sqid>_<type>_<slug>.md
FILENAME_PATTERN = re.compile(
    r'^(?P<mp>\d{3}(?:-\d{3})*)_'
    r'(?P<sqid>[A-Za-z0-9]+)_'
    r'(?P<type>[a-z]+)'
    r'(?:_(?P<slug>.+))?\.md$'
)


class ValidationResult(TypedDict):
    """Result of validation operation."""

    valid: bool
    violations: list[str]
    repaired: list[str]


class ValidateOutlineUseCase:
    """Use case for validating outline integrity and repairing common issues."""

    def __init__(self, filesystem: FileSystemPort) -> None:
        """Initialize use case with filesystem adapter.

        Args:
            filesystem: Filesystem port implementation

        """
        self.filesystem = filesystem

    def execute(self, directory: Path, repair: bool = False) -> ValidationResult:  # noqa: FBT001, FBT002
        """Validate outline and optionally repair issues.

        Args:
            directory: Working directory for outline
            repair: If True, auto-repair common issues

        Returns:
            ValidationResult with valid status, violations, and repairs performed

        """
        # Build outline from filesystem (also detects filesystem-level issues)
        outline, fs_violations = self._build_outline(directory)

        # Validate invariants
        violations = fs_violations + outline.validate_invariants()

        # Track repairs
        repaired: list[str] = []

        # If repair requested, fix common issues
        if repair and violations:
            repaired = self._repair_issues(outline, directory)

            # Re-validate after repairs
            violations = outline.validate_invariants()

        return ValidationResult(valid=len(violations) == 0, violations=violations, repaired=repaired)

    def _build_outline(self, directory: Path) -> tuple[Outline, list[str]]:  # noqa: PLR0914, C901, PLR0912
        """Build Outline from filesystem.

        Args:
            directory: Working directory

        Returns:
            Tuple of (Outline with all nodes loaded from files, list of filesystem violations)

        """
        from linemark.domain.entities import SQID, MaterializedPath, Node, Outline

        all_files = self.filesystem.list_markdown_files(directory)
        nodes: dict[str, Node] = {}
        fs_violations: list[str] = []

        # Track SQIDs we've seen to detect duplicates
        seen_sqids: set[str] = set()
        sqid_files: dict[str, list[str]] = {}

        for filepath in all_files:
            match = FILENAME_PATTERN.match(filepath.name)
            if not match:
                continue  # pragma: no cover

            sqid_str = match.group('sqid')

            # Track files for this SQID to detect duplicates
            if sqid_str not in sqid_files:
                sqid_files[sqid_str] = []
            sqid_files[sqid_str].append(filepath.name)

            # Skip if we've already processed this SQID
            if sqid_str in seen_sqids:
                continue

            seen_sqids.add(sqid_str)

            # Parse node details from draft file
            mp_str = match.group('mp')
            slug = match.group('slug')

            # Read title from draft file
            draft_path = directory / f'{mp_str}_{sqid_str}_draft_{slug}.md'
            if self.filesystem.file_exists(draft_path):
                content = self.filesystem.read_file(draft_path)
                parts = content.split('---')
                if len(parts) >= 3:  # noqa: PLR2004
                    frontmatter = yaml.safe_load(parts[1])
                    title = frontmatter.get('title', 'Untitled')
                else:
                    title = 'Untitled'  # pragma: no cover
            else:  # pragma: no cover
                title = 'Untitled'  # pragma: no cover

            # Find all document types for this node
            node_files = [f for f in all_files if f'_{sqid_str}_' in f.name]
            doc_types = set()
            for nf in node_files:
                nf_match = FILENAME_PATTERN.match(nf.name)
                if nf_match:  # pragma: no branch
                    doc_types.add(nf_match.group('type'))

            # Create node
            node = Node(
                sqid=SQID(value=sqid_str),
                mp=MaterializedPath.from_string(mp_str),
                title=title,
                slug=slug or '',
                document_types=doc_types,
            )

            nodes[sqid_str] = node

        # Check for duplicate SQIDs with different MPs (filesystem corruption)
        for sqid_str, files in sqid_files.items():
            # Extract MPs from filenames
            mps_for_sqid = set()
            for filename in files:
                match = FILENAME_PATTERN.match(filename)
                if match:  # pragma: no branch
                    mps_for_sqid.add(match.group('mp'))

            if len(mps_for_sqid) > 1:
                fs_violations.append(
                    f'Duplicate SQID {sqid_str} found with different materialized paths: '
                    f'{", ".join(sorted(mps_for_sqid))}'
                )

        return Outline(nodes=nodes), fs_violations

    def _repair_issues(self, outline: Outline, directory: Path) -> list[str]:
        """Repair common outline issues.

        Args:
            outline: Outline to repair
            directory: Working directory

        Returns:
            List of repair messages

        """
        repaired: list[str] = []

        # Repair missing required document types
        for node in outline.nodes.values():
            required_types = {'draft', 'notes'}
            missing_types = required_types - node.document_types

            for doc_type in missing_types:
                # Create empty file for missing type
                filename = node.filename(doc_type)
                filepath = directory / filename

                if not self.filesystem.file_exists(filepath):  # pragma: no branch
                    # Create empty content (draft gets frontmatter, notes is empty)
                    content = f'---\ntitle: {node.title}\n---\n' if doc_type == 'draft' else ''

                    self.filesystem.write_file(filepath, content)
                    node.document_types.add(doc_type)
                    repaired.append(f'Created missing {doc_type} file for node @{node.sqid.value}')

        return repaired
