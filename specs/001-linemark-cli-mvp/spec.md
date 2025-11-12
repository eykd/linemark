# Feature Specification: Linemark - Hierarchical Markdown Outline Manager

**Feature Branch**: `001-linemark-cli-mvp`
**Created**: 2025-11-12
**Status**: Draft
**Input**: User description: "Linemark is a command-line tool for managing hierarchical outlines of Markdown documents using filenames alone. It enables structured, sortable, and human-readable content organization within a flat directory."

## Clarifications

### Session 2025-11-12

- Q: Where is the global monotonic SQID counter persisted between tool invocations? → A: Derive counter from highest SQID found by scanning all existing files at startup
- Q: Where does the tool look for the outline directory? → A: Current working directory by default, with optional --directory flag on all commands to specify a different location
- Q: What happens when a materialized path segment reaches 999 and needs another child added? → A: Return error message with guidance to run `lmk compact` or restructure hierarchy
- Q: How does the system handle concurrent modifications (two users/processes modifying the same outline)? → A: Optimistic approach - no locking, rely on filesystem atomicity and git for conflict resolution
- Q: How should the system handle filesystem errors (locked files, permissions, interrupted operations)? → A: Fail fast with descriptive error message, preserve existing state, no automatic rollback

## User Scenarios & Testing

### User Story 1 - Create and Organize Outline Nodes (Priority: P1)

Writers and content creators need to quickly build hierarchical outlines for their writing projects (novels, documentation, research) without managing complex folder structures. They want to add chapters, sections, and subsections with meaningful titles while the system handles the organizational details behind the scenes.

**Why this priority**: This is the foundational capability - without the ability to create and organize nodes, no other features matter. It delivers immediate value by letting users structure their content.

**Independent Test**: Can be fully tested by creating a new empty directory, adding several nodes with `lmk add`, and verifying files are created with proper naming and hierarchy. Delivers value by enabling basic outline creation.

**Acceptance Scenarios**:

1. **Given** an empty directory, **When** user runs `lmk add "Chapter One"`, **Then** two files are created: one for draft content with the title in frontmatter, and one for notes, both with proper materialized path (001) and unique identifiers
2. **Given** an existing root node (@A1b2C), **When** user runs `lmk add --child-of @A1b2C "Section 1.1"`, **Then** a child node is created with materialized path showing parent-child relationship (e.g., 001-100)
3. **Given** two sibling nodes, **When** user runs `lmk add --sibling-of @B3x9k --before @B3x9k "New Chapter"`, **Then** the new node is inserted with a materialized path between the siblings
4. **Given** multiple nodes, **When** user runs `lmk list`, **Then** a tree view displays showing the hierarchy with titles and identifiers in correct order

---

### User Story 2 - Reorganize Content Structure (Priority: P2)

As content evolves, writers need to restructure their outlines by moving sections to different locations without losing their work or manually renaming files. They want to move a chapter with all its sections as a unit.

**Why this priority**: Content reorganization is a common need during the writing process. While not needed for initial outline creation, it becomes critical once users start refining structure.

**Independent Test**: Can be tested by creating a multi-level outline, moving a node with children, and verifying all affected files are renamed correctly while preserving content and hierarchy relationships.

**Acceptance Scenarios**:

1. **Given** a node with children, **When** user runs `lmk move @SQID --to @NewParent`, **Then** the node and all its descendants are relocated, with materialized paths updated to reflect the new position
2. **Given** two sibling nodes, **When** user runs `lmk move @SQID --to @Sibling --before`, **Then** the node is repositioned before the target sibling, with materialized path renumbered appropriately
3. **Given** a deeply nested node (depth 5+), **When** moved to a different parent, **Then** all descendant files are renamed with new path prefixes while unique identifiers remain unchanged
4. **Given** a move operation affecting 50+ files, **When** executed, **Then** all renames complete without file name collisions or data loss

---

### User Story 3 - Maintain Multiple Document Types per Node (Priority: P2)

Writers working on complex projects (like novels with character sheets, or documentation with examples) need to keep different types of content associated with each outline node - the main draft, research notes, character profiles, or technical specifications.

**Why this priority**: Multi-document support is a key differentiator but not required for basic outlining. It enables richer content organization for advanced use cases.

**Independent Test**: Can be tested by creating a node, adding various document types to it, listing types, and removing types - all verifiable through filesystem and `lmk types` commands.

**Acceptance Scenarios**:

1. **Given** a newly created node, **When** user runs `lmk types list @SQID`, **Then** both `draft` and `notes` types are shown as existing
2. **Given** an existing node, **When** user runs `lmk types add characters @SQID`, **Then** a new empty markdown file is created with the `characters` document type
3. **Given** a node with multiple types, **When** user runs `lmk types remove characters @SQID`, **Then** only the characters file is deleted, leaving draft and notes intact
4. **Given** multiple document types on a node, **When** the node is moved or renamed, **Then** all document type files are updated consistently

---

### User Story 4 - Rename Nodes and Update Titles (Priority: P3)

As content develops, writers need to refine node titles to better reflect their content, and want filenames to automatically stay synchronized with the canonical title.

**Why this priority**: Renaming is useful but not critical for initial development. Users can work with initial titles and refine later.

**Independent Test**: Can be tested by creating a node, renaming it, and verifying both the frontmatter title and all associated filenames are updated correctly.

**Acceptance Scenarios**:

1. **Given** a node with title "Chapter One", **When** user runs `lmk rename @SQID "Introduction"`, **Then** the frontmatter title is updated and all associated filenames reflect the new slug
2. **Given** a node with special characters in title, **When** renamed to "Writer's Guide: Advanced!", **Then** the slug is properly formatted as "Writers-Guide-Advanced" in filenames
3. **Given** a node with multiple document types, **When** renamed, **Then** all document type files receive the updated slug
4. **Given** a rename operation, **When** completed, **Then** the unique identifier (SQID) remains unchanged

---

### User Story 5 - Remove Unwanted Content (Priority: P3)

Writers need to clean up their outlines by removing abandoned sections, with options to either delete entire subtrees or preserve child content by promoting it up a level.

**Why this priority**: Deletion is needed but less urgent than creation and organization. Most users will focus on building content initially.

**Independent Test**: Can be tested by creating a node hierarchy, deleting nodes with different options (recursive, promote), and verifying correct files are removed and children are handled appropriately.

**Acceptance Scenarios**:

1. **Given** a leaf node (no children), **When** user runs `lmk delete @SQID` and confirms, **Then** all files for that node are permanently deleted
2. **Given** a node with children, **When** user runs `lmk delete @SQID -r` and confirms, **Then** the node and all descendants are deleted
3. **Given** a node with children, **When** user runs `lmk delete @SQID -p`, **Then** the node is deleted and children are promoted to the parent's level with renumbered paths
4. **Given** any delete operation, **When** user runs it without --force, **Then** an interactive confirmation prompt appears before deletion
5. **Given** a delete operation, **When** confirmed, **Then** no temporary or backup files are created (user relies on version control)

---

### User Story 6 - Restore Ideal Numbering Spacing (Priority: P4)

After many insertions and reorganizations, writers want to restore clean, evenly-spaced numbering in their materialized paths to maintain readability and ensure room for future insertions.

**Why this priority**: This is a maintenance/housekeeping operation that can be deferred. Outlines function correctly with any valid numbering scheme.

**Independent Test**: Can be tested by creating an outline with irregular numbering, running compact, and verifying paths are renumbered with ideal spacing while maintaining hierarchy.

**Acceptance Scenarios**:

1. **Given** an outline with irregular numbering (e.g., 001, 003, 007), **When** user runs `lmk compact`, **Then** siblings are renumbered with 100-unit spacing (001, 100, 200)
2. **Given** a specific subtree, **When** user runs `lmk compact @SQID`, **Then** only that subtree's numbering is compacted, leaving other parts unchanged
3. **Given** a multi-level hierarchy, **When** compacted, **Then** all levels use tiered numbering (100s for major, 10s for medium, 1s for fine-grained)
4. **Given** a compact operation affecting many files, **When** completed, **Then** a summary shows number of files renamed

---

### User Story 7 - Validate and Repair Outline Integrity (Priority: P4)

Users who manually edit files or experience interrupted operations want a way to detect and automatically fix structural problems in their outline (duplicate identifiers, invalid naming, orphaned files).

**Why this priority**: This is a safety net and recovery tool. Most users won't need it if they use the CLI exclusively, but it provides confidence for advanced scenarios.

**Independent Test**: Can be tested by intentionally creating various invalid states (duplicate SQIDs, malformed filenames), running doctor, and verifying automatic repairs or clear error messages.

**Acceptance Scenarios**:

1. **Given** two files with the same SQID, **When** user runs `lmk doctor`, **Then** one SQID is regenerated and files are renamed accordingly
2. **Given** a file with missing SQID, **When** doctor runs, **Then** a new unique SQID is assigned
3. **Given** files with invalid materialized path format, **When** doctor runs, **Then** they are either renamed to valid format or flagged for manual review
4. **Given** a node missing required `draft` or `notes` files, **When** doctor runs, **Then** missing files are created with appropriate defaults
5. **Given** a fully valid outline, **When** doctor runs, **Then** a success message confirms no issues found

---

### User Story 8 - View Outline in Different Formats (Priority: P4)

Users want to view their outline structure both as a visual tree for quick browsing and as structured JSON data for integration with other tools or scripts.

**Why this priority**: Alternative output formats are nice-to-have enhancements. The default tree view serves most user needs.

**Independent Test**: Can be tested by creating an outline and running `lmk list` with and without `--json` flag, verifying correct formatting in both cases.

**Acceptance Scenarios**:

1. **Given** any outline, **When** user runs `lmk list`, **Then** a human-readable tree is displayed with proper indentation and node titles
2. **Given** any outline, **When** user runs `lmk list --json`, **Then** valid JSON is output with nested `children` arrays representing hierarchy
3. **Given** a large outline (100+ nodes), **When** listed, **Then** output renders within 2 seconds
4. **Given** nodes with multiple document types, **When** listed, **Then** the output indicates available document types for each node

---

### Edge Cases

- **Materialized path segment limit (999)**: When a materialized path segment reaches 999 and another child needs to be added, the system returns an error message instructing the user to run `lmk compact` to restore spacing or restructure the hierarchy to reduce sibling count at that level.
- **Concurrent modifications**: The system uses an optimistic approach without file locking. Multiple processes can modify the same outline simultaneously. The system relies on filesystem atomicity for individual file operations and expects users to use version control (git) for conflict resolution if needed. The self-healing SQID counter (derived from existing files) prevents duplicate identifier generation.
- **Filesystem errors (locked files, permissions, interrupted operations)**: The system uses a fail-fast approach. When encountering filesystem errors (locked files, permission denied, disk full, etc.), operations immediately terminate with a descriptive error message indicating the specific failure. No automatic retry or rollback is performed. Users rely on version control (git) to recover from partial states if needed.
- What happens when moving a node would create a materialized path that already exists?
- How does the system behave when the SQID counter reaches its maximum value?
- What happens if a user manually renames files incorrectly while the tool is running?
- How does the system handle Unicode or emoji characters in node titles?
- How does the system handle case-sensitive vs case-insensitive filesystems?

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate unique, stable alphanumeric identifiers (SQIDs) for each node that persist across renames and moves
- **FR-002**: System MUST encode hierarchy using materialized paths with three-digit, zero-padded segments (001-999) separated by dashes
- **FR-003**: System MUST create both a `draft` and `notes` markdown file whenever a new node is added
- **FR-004**: System MUST store the canonical node title in YAML frontmatter of the `draft` file with key `title`
- **FR-005**: System MUST generate URL-friendly slugs from titles for use in filenames
- **FR-006**: System MUST allow nodes to be identified by either SQID (prefixed with @) or materialized path
- **FR-007**: System MUST support adding new nodes as children or siblings of existing nodes
- **FR-008**: System MUST support positional placement (before/after) when adding sibling nodes
- **FR-009**: System MUST default to placing new children as last child and new siblings as immediately after reference node
- **FR-010**: System MUST update materialized paths of all descendants when moving a node
- **FR-011**: System MUST preserve SQIDs when moving or renaming nodes
- **FR-012**: System MUST handle batch file renames to avoid naming collisions during moves
- **FR-013**: System MUST delete all files associated with a node when deleting
- **FR-014**: System MUST support recursive deletion of entire subtrees
- **FR-015**: System MUST support promoting children to parent level when deleting a node
- **FR-016**: System MUST require interactive confirmation for all delete operations unless --force flag is used
- **FR-017**: System MUST update both frontmatter title and filename slugs when renaming a node
- **FR-018**: System MUST support adding arbitrary document type files to existing nodes
- **FR-019**: System MUST support removing specific document type files from nodes
- **FR-020**: System MUST support listing all document types associated with a node
- **FR-021**: System MUST display outline hierarchy in tree format by default
- **FR-022**: System MUST support JSON output format with nested children arrays
- **FR-023**: System MUST support renumbering materialized paths with tiered spacing (100/10/1)
- **FR-024**: System MUST support compact operation on entire outline or specific subtree
- **FR-025**: System MUST detect and repair duplicate SQIDs
- **FR-026**: System MUST detect and assign SQIDs to files missing them
- **FR-027**: System MUST detect and repair invalid filename formats
- **FR-028**: System MUST detect and create missing required document types (draft, notes)
- **FR-029**: System MUST validate three-digit format and dash separators in materialized paths
- **FR-030**: System MUST parse filenames using pattern: `<mp>_<sqid>_<type>_<optional-slug>.md`
- **FR-031**: System MUST sort nodes lexicographically by materialized path
- **FR-032**: System MUST maintain a global monotonic counter for SQID generation by scanning all existing files at startup and deriving the counter from the highest SQID found (plus one)
- **FR-033**: System MUST operate on a single flat directory (no nested folders), using the current working directory by default, with optional --directory flag supported on all commands to specify an alternative location
- **FR-034**: System MUST print created filenames when adding nodes
- **FR-035**: System MUST print summary of renames when running compact operation
- **FR-036**: System MUST accept command-line flags for all options (no external config files in MVP)
- **FR-037**: System MUST support materialized path depths of at least 5 levels
- **FR-038**: System MUST handle node titles containing special characters by proper slugification
- **FR-039**: System MUST support a --directory flag on all commands to specify an alternative working directory instead of using the current working directory
- **FR-040**: System MUST return a clear error message when attempting to add a child to a node whose materialized path segment has reached 999, instructing the user to run `lmk compact` or restructure the hierarchy
- **FR-041**: System MUST NOT implement file locking mechanisms, using an optimistic concurrency approach that relies on filesystem atomicity and expects users to coordinate through version control for conflict resolution
- **FR-042**: System MUST use a fail-fast error handling approach, immediately terminating operations with descriptive error messages when filesystem errors occur (locked files, permission denied, disk full), without automatic retry or rollback mechanisms

### Key Entities

- **Node**: A logical entry in the outline hierarchy, identified by a unique SQID and positioned by a materialized path. Contains one or more markdown files of different document types. The node's canonical title is stored in the YAML frontmatter of its `draft` file.

- **Materialized Path (MP)**: A sequence of three-digit integers (001-999) joined by dashes that encodes a node's position in the hierarchy and sibling order. Example: `001-100-050` represents the root node's 1st child's 50th child. Determines lexicographic sort order.

- **SQID**: A short, URL-safe alphanumeric identifier generated by the sqids library that uniquely identifies a node. Remains stable across all renames and moves. Generated from a monotonically increasing counter that is derived at startup by scanning all existing files and using the highest SQID value found plus one.

- **Document Type**: A category of content associated with a node (e.g., `draft`, `notes`, `characters`). Each document type corresponds to one markdown file. Required types are `draft` (contains YAML frontmatter with title) and `notes` (empty by default).

- **Outline**: The complete hierarchical structure of all nodes in a directory, represented by the collection of markdown files following the naming convention. Encoded entirely in filenames with no external database.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can create a new outline node with title in under 5 seconds using a single command
- **SC-002**: Users can visualize a 100-node outline hierarchy by running one command that completes in under 2 seconds
- **SC-003**: Users can reorganize a node with 10+ descendants without data loss, completing in under 10 seconds
- **SC-004**: System can manage outlines with at least 1,000 nodes without performance degradation
- **SC-005**: Files can be sorted alphabetically in any file browser and display in correct hierarchical order
- **SC-006**: 100% of file operations (moves, renames, deletes) preserve node unique identifiers
- **SC-007**: Users can identify any node using a short identifier (under 10 characters) that never changes
- **SC-008**: Outline structure can be imported/understood by common markdown tools (Obsidian, VS Code) without special plugins
- **SC-009**: All destructive operations require explicit confirmation, preventing accidental data loss
- **SC-010**: System detects and repairs structural inconsistencies automatically when validation is run
- **SC-011**: Users can recover from errors by using version control (git) without special tool support
- **SC-012**: New users can create their first 3-level outline within 5 minutes of reading basic documentation
