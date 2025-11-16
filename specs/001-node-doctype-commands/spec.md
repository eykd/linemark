# Feature Specification: Node and Document Type Operations

**Feature Branch**: `001-node-doctype-commands`
**Created**: 2025-11-15
**Status**: Draft
**Input**: User description: "We now need a series of commands for working with individual nodes and doctypes: types read, types write, and search"

## Clarifications

### Session 2025-11-15

- Q: When `lmk types write` receives empty stdin, how should it behave? → A: Create/update the document type with empty body content (blank file) - following standard Unix tool behavior
- Q: When `lmk search` returns multiple results, in what order should they be displayed? → A: By outline position (respecting the node hierarchy/order in the outline)
- Q: Should `lmk search` be case-sensitive or case-insensitive by default? → A: Case-insensitive by default, with an optional --case-sensitive flag for precision matching
- Q: When `lmk types write` updates an existing document type file, how should it handle the write operation to ensure data safety? → A: Atomic write (write to temp file, then rename to replace original)
- Q: How should `lmk search` handle regex patterns that could match across multiple lines? → A: Line-by-line matching by default (aligned with Python's `re` module default behavior), with optional `--multiline` flag to enable cross-line matching (like `re.DOTALL`)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read Document Type Content (Priority: P1)

A user needs to view the content of a specific document type for a node to review or reference the information without modifying it.

**Why this priority**: Reading content is the most fundamental operation and required for all other workflows. Users need to inspect content before editing, searching, or making decisions.

**Independent Test**: Can be fully tested by creating a node with a specific document type (e.g., "characters"), writing content to it, and verifying that the read command returns the exact content without requiring any other commands to function.

**Acceptance Scenarios**:

1. **Given** a node exists with SQID @ABC123 and has a "characters" document type with content, **When** user runs `lmk types read characters @ABC123`, **Then** the system displays the body content of the characters document type file
2. **Given** a node exists with SQID @XYZ789 and has a "notes" document type, **When** user runs `lmk types read notes @XYZ789`, **Then** the system displays the body content excluding the YAML frontmatter
3. **Given** a node exists but does not have the requested document type, **When** user runs `lmk types read missing-type @ABC123`, **Then** the system displays an appropriate error message indicating the document type does not exist for this node

---

### User Story 2 - Write Document Type Content (Priority: P2)

A user needs to create or update the content of a specific document type for a node by providing input from stdin, enabling scripting and automation workflows.

**Why this priority**: Writing content is essential for content creation and updates, but depends on the ability to verify changes (via read). This enables automated workflows and bulk operations.

**Independent Test**: Can be fully tested by piping content to the write command and verifying the file is created/updated correctly with the provided content, independently testable through filesystem inspection.

**Acceptance Scenarios**:

1. **Given** a node exists with SQID @ABC123, **When** user runs `echo "New content" | lmk types write characters @ABC123`, **Then** the system creates or updates the characters document type file with "New content" as the body
2. **Given** a node exists with SQID @ABC123 and already has a characters document type with existing content, **When** user provides new content via stdin to `lmk types write characters @ABC123`, **Then** the system replaces the existing body content with the new content while preserving the YAML frontmatter
3. **Given** a node exists with SQID @ABC123, **When** user runs `lmk types write characters @ABC123 << EOF` followed by multi-line content and `EOF`, **Then** the system writes all lines between the heredoc delimiters to the document type file
4. **Given** a node exists with SQID @ABC123, **When** user runs `echo "" | lmk types write characters @ABC123` or provides empty stdin, **Then** the system creates/updates the document type with empty body content
5. **Given** an invalid SQID is provided, **When** user attempts to write content, **Then** the system displays an error message indicating the node does not exist

---

### User Story 3 - Search Across Nodes (Priority: P3)

A user needs to find specific content across multiple nodes in the outline using regex patterns, optionally filtering by subtree and document type to locate information quickly.

**Why this priority**: Search is a discovery and navigation tool that builds on the read capability. It's valuable but not required for basic content operations. Users can manually read individual files if search is not available.

**Independent Test**: Can be fully tested by creating multiple nodes with known content patterns, running search queries with various filters, and verifying the results match expected nodes and line numbers independently of other commands.

**Acceptance Scenarios**:

1. **Given** multiple nodes exist with various content, **When** user runs `lmk search "foo"`, **Then** the system displays all matching lines across all nodes with format "@SQID: filename\nLINE_NUM: line content", ordered by outline position
2. **Given** multiple nodes exist in a subtree starting at @ABC123, **When** user runs `lmk search @ABC123 "bar"`, **Then** the system displays only matches within the subtree rooted at @ABC123
3. **Given** nodes have multiple document types (notes, characters, etc.), **When** user runs `lmk search --doctype=notes --doctype=characters @ABC123 "pattern"`, **Then** the system displays only matches from the specified document types within the subtree
4. **Given** a search pattern contains regex special characters, **When** user runs `lmk search --literal "foo*"`, **Then** the system treats the pattern as a literal string and finds exact matches including the asterisk
5. **Given** a user needs structured output, **When** user runs `lmk search --json "pattern"`, **Then** the system returns results in JSON format instead of plaintext
6. **Given** a regex pattern that matches content, **When** user runs `lmk search "log.*Error"`, **Then** the system uses case-insensitive regex matching to find all lines matching the pattern
7. **Given** content with mixed case, **When** user runs `lmk search --case-sensitive "Error"`, **Then** the system returns only matches with exact case ("Error"), not "error" or "ERROR"
8. **Given** content that spans multiple lines, **When** user runs `lmk search --multiline "start.*end"`, **Then** the system matches patterns across line boundaries (like Python's `re.DOTALL`)

---

### Edge Cases

- What happens when a node has no document type files at all?
- What happens when the SQID format is invalid (missing @ prefix or wrong encoding)?
- When stdin is empty for the write command, the system creates/updates the document type with empty body content (following standard Unix tool behavior like `cat`, `tee`)
- How does the system handle very large document bodies (MB+ of content) for read operations?
- What happens when a search pattern is an invalid regex?
- How does the system handle special characters in document type names?
- What happens when the working directory does not exist or is not a valid linemark project?
- By default, search matches line-by-line (patterns cannot span multiple lines); use `--multiline` flag to enable cross-line matching
- When attempting to write to a read-only filesystem, the atomic write operation will fail and the original file remains intact
- If a write operation is interrupted (disk full, process killed), the original file remains intact due to atomic write (temp-then-rename) approach
- How does the system handle Unicode content in document bodies?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read the body content of a specified document type for a given node SQID
- **FR-002**: System MUST exclude YAML frontmatter when displaying document body content via the read command
- **FR-003**: System MUST accept content from stdin and write it to the body of a specified document type for a given node SQID
- **FR-004**: System MUST preserve existing YAML frontmatter when updating document body content via the write command
- **FR-004a**: System MUST use atomic write operations (write to temp file, then rename) when updating existing document type files to ensure data integrity
- **FR-005**: System MUST support heredoc syntax (e.g., `<< EOF`) for multi-line content input to the write command
- **FR-005a**: System MUST accept empty stdin for the write command and create/update the document type with empty body content
- **FR-006**: System MUST search across all nodes in the outline for content matching a regex pattern (case-insensitive by default, line-by-line matching)
- **FR-006a**: System MUST provide a `--case-sensitive` flag to enable case-sensitive pattern matching
- **FR-006b**: System MUST provide a `--multiline` flag to enable cross-line pattern matching (aligning with Python's `re.DOTALL` behavior)
- **FR-007**: System MUST support filtering search results by subtree when a SQID is provided as a search scope
- **FR-008**: System MUST support filtering search results by one or more document types via `--doctype` option
- **FR-009**: System MUST display search results in the format "@SQID: filename\nLINE_NUMBER: line content"
- **FR-009a**: System MUST order search results by outline position (respecting the node hierarchy/order in the outline)
- **FR-010**: System MUST support literal string matching (non-regex) via the `--literal` option for search
- **FR-011**: System MUST support JSON output format for search results via the `--json` option
- **FR-012**: System MUST accept a `--directory` option to specify the working directory for all three commands
- **FR-013**: System MUST default to the current directory when `--directory` is not specified
- **FR-014**: System MUST validate that the provided SQID exists and is in the correct format (@SQID notation)
- **FR-015**: System MUST display appropriate error messages when a node or document type does not exist
- **FR-016**: System MUST handle invalid regex patterns gracefully with clear error messages
- **FR-017**: System MUST display help text with examples when `--help` is invoked for any command

### Key Entities

- **Node**: Represents a single outline item identified by a unique SQID, may have multiple document type files
- **Document Type**: A categorization of content (e.g., "notes", "characters", "scenes") associated with a node, stored as a separate file with YAML frontmatter and body content
- **SQID**: Short unique identifier in @SQID format (e.g., @ABC123) used to reference nodes
- **Subtree**: A hierarchical portion of the outline starting from a specific node and including all its descendants
- **Search Result**: A match found in the outline containing the SQID, filename, line number, and matching line content

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can read any document type content for any valid node in under 2 seconds
- **SC-002**: Users can write content to any document type for any valid node in under 3 seconds
- **SC-003**: Users can search across 1000+ nodes and receive results in under 5 seconds
- **SC-004**: Search accurately returns all matches with correct line numbers and content
- **SC-005**: Write operations preserve 100% of existing YAML frontmatter without corruption
- **SC-005a**: Interrupted or failed write operations leave the original file intact with no data loss (atomic write guarantee)
- **SC-006**: All three commands provide clear, actionable error messages for invalid inputs (invalid SQID, missing files, invalid regex)
- **SC-007**: Users can successfully pipe content from one command to another (e.g., `lmk types read notes @A | process | lmk types write notes @B`)
- **SC-008**: Users can complete common workflows (read → edit → write, search → read) without consulting documentation after initial learning
