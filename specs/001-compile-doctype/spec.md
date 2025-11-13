# Feature Specification: Compile Doctype Command

**Feature Branch**: `001-compile-doctype`
**Created**: 2025-11-13
**Status**: Draft
**Input**: User description: "Let's add a new command `lmk compile <doctype> <optional-SQID>` which will concatenate all the content for doctypes of a type for the specified subtree, or lacking a SQID, for the entire forest outline, concatenating all of the specified doctype in the forest or subtree from top to bottom, depth first (i.e. the same as lexicographical ordering based on the materialized paths). So `lmk compile draft` would concatenate all the `draft` doctypes, resulting in a draft-order compilation of the entire draft. If any nodes are missing that doctype, simply leave it out. For all the node docs that are included in the compilation, insert '\n\n---\n\n' between them in the concatenation, with a `--separator` CLI argument to specify another string besides '---'."

## Clarifications

### Session 2025-11-13

- Q: When compiling a subtree where the root node (specified by SQID) contains a matching doctype, should that root node's content be included in the compilation? → A: Root node's doctype IS included (if it exists) - subtree = node + descendants
- Q: When a compilation results in no content (e.g., empty forest, no matching doctypes, or SQID subtree has no matching doctypes), what should the command output? → A: Output nothing (empty string) and exit successfully - silent success
- Q: When a node has a doctype file that exists but is completely empty (0 bytes or only whitespace), should that empty content be included in the compilation? → A: Skip empty files entirely - treat same as missing doctype (no separator added)
- Q: How should the command handle custom separators that contain special shell characters or escape sequences (e.g., `\n`, `\t`, literal backslashes)? → A: Interpret escape sequences (`\n` → newline, `\t` → tab, etc.) - standard CLI behavior
- Q: When validating whether a provided doctype name is valid, what constitutes a "valid doctype name" in the system? → A: Doctype must exist in at least one node - validate against actual forest content

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compile Entire Forest by Doctype (Priority: P1)

A user wants to generate a single, cohesive document by combining all content of a specific doctype (e.g., "draft", "notes", "summary") from the entire forest outline in hierarchical order.

**Why this priority**: This is the core functionality of the feature - enabling users to export/view all content of a type in a single, ordered document. This is essential for reviewing, exporting, or sharing compiled content.

**Independent Test**: Can be fully tested by running `lmk compile draft` on a forest with multiple nodes containing draft doctypes and verifying the output is a concatenated document in depth-first order.

**Acceptance Scenarios**:

1. **Given** a forest with multiple nodes each containing a "draft" doctype, **When** user runs `lmk compile draft`, **Then** all draft content is concatenated in depth-first (lexicographical materialized path) order with separators between each document
2. **Given** a forest where some nodes lack the specified doctype, **When** user runs `lmk compile draft`, **Then** only nodes with draft content are included, others are skipped silently
3. **Given** a forest where the "notes" doctype exists but all instances are empty files, **When** user runs `lmk compile notes`, **Then** command outputs empty string to stdout and exits successfully (exit code 0)
4. **Given** a forest where the "invalid-type" doctype does not exist in any node, **When** user runs `lmk compile invalid-type`, **Then** command provides error message indicating the doctype was not found

---

### User Story 2 - Compile Subtree by Doctype (Priority: P2)

A user wants to compile content from a specific subtree of the forest by providing a SQID identifier, limiting the scope to that node (if it has the doctype) and all its descendants.

**Why this priority**: This provides targeted compilation for working with specific sections, which is important for modular work but secondary to the full forest compilation capability.

**Independent Test**: Can be fully tested by running `lmk compile draft SQID123` on a forest where SQID123 has children, and verifying only that subtree's content (including the root node if it has the doctype) appears in the output.

**Acceptance Scenarios**:

1. **Given** a node with SQID "abc123" that has a "draft" doctype and child nodes with "draft" doctypes, **When** user runs `lmk compile draft abc123`, **Then** draft content from the specified node AND its descendants is compiled in depth-first order
2. **Given** a valid SQID for a leaf node with no children but with the specified doctype, **When** user runs `lmk compile draft SQID`, **Then** only that single node's draft content is output
3. **Given** an invalid or non-existent SQID, **When** user runs `lmk compile draft invalid-sqid`, **Then** command provides clear error message indicating the SQID was not found
4. **Given** a valid SQID but the doctype does not exist in that subtree, **When** user runs `lmk compile notes SQID`, **Then** command provides error message indicating the doctype was not found in the specified subtree

---

### User Story 3 - Custom Separator Between Documents (Priority: P3)

A user wants to customize the separator used between concatenated documents instead of the default "---" to match their output format needs (e.g., for markdown, LaTeX, or other document types).

**Why this priority**: This enhances flexibility for different use cases but is not essential for basic functionality. Users can work with default separators initially.

**Independent Test**: Can be fully tested by running `lmk compile draft --separator "===PAGE BREAK==="` and verifying the custom separator appears between documents.

**Acceptance Scenarios**:

1. **Given** a forest with multiple draft doctypes, **When** user runs `lmk compile draft --separator "===BREAK==="`, **Then** the output uses "===BREAK===" instead of "---" between documents
2. **Given** a custom separator with escape sequences like `\n` or `\t`, **When** user provides it via `--separator` flag, **Then** the escape sequences are interpreted as their literal characters (newline, tab, etc.)
3. **Given** no separator flag is provided, **When** user runs `lmk compile draft`, **Then** the default separator '\n\n---\n\n' is used between documents

---

### Edge Cases

- What happens when a doctype name doesn't exist anywhere in the forest/subtree? (Answer: error message indicating doctype not found)
- What happens when a SQID is provided but that node and its subtree have the doctype files but they're all empty? (Answer: outputs empty string, exit code 0)
- How does the system handle nodes with empty doctype files (0 bytes or only whitespace)? (Answer: skipped entirely, treated same as missing doctype - no separator added)
- What happens when separator contains escape sequences like `\n`, `\t`? (Answer: interpreted as literal characters - newline, tab, etc.)
- How does the command behave when the forest outline is corrupted or has inconsistent materialized paths?
- What if doctype files contain different encodings or character sets?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a doctype argument specifying which document type to compile
- **FR-002**: System MUST accept an optional SQID argument to limit compilation to a specific subtree (the specified node and all its descendants)
- **FR-003**: System MUST traverse nodes in depth-first order matching lexicographical ordering of materialized paths
- **FR-004**: System MUST concatenate all matching doctype content from traversed nodes
- **FR-005**: System MUST insert '\n\n---\n\n' as separator between concatenated documents by default
- **FR-006**: System MUST support a `--separator` flag allowing users to specify custom separator text with escape sequence interpretation (e.g., `\n` → newline, `\t` → tab)
- **FR-007**: System MUST silently skip nodes that lack the specified doctype or have empty/whitespace-only doctype files
- **FR-008**: System MUST output the compiled result to stdout
- **FR-009**: System MUST provide informative error messages for invalid SQID values
- **FR-010**: System MUST output empty string (no content) when doctype exists but all instances are empty/whitespace-only, and exit successfully with code 0
- **FR-011**: Command MUST validate that the provided doctype file exists in at least one node in the compilation scope (forest or subtree) and provide clear error message if the doctype does not exist

### Key Entities

- **Doctype**: A document type category (e.g., "draft", "notes", "summary") that exists as separate files within nodes
- **Node**: An element in the forest outline hierarchy containing zero or more doctype documents
- **Subtree**: When a SQID is specified, includes the specified node itself (if it has the doctype) plus all its descendant nodes
- **Materialized Path**: The hierarchical path identifier for each node used for ordering
- **Compiled Output**: The concatenated result of all matching doctype content with separators

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can compile all doctypes from entire forest with a single command execution
- **SC-002**: Users can compile doctypes from any subtree by providing a SQID identifier
- **SC-003**: Compiled output maintains correct hierarchical ordering matching the forest structure
- **SC-004**: Users can customize document separators to match their workflow needs
- **SC-005**: Command completes successfully with empty output when doctype exists but all instances are empty
- **SC-006**: Users receive clear, actionable error messages for invalid inputs (invalid SQID, non-existent doctype)
- **SC-007**: Typos in doctype names are caught early with validation against actual forest content
