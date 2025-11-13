# Feature Specification: Enhanced List Command with Subtree Filtering and Metadata Display

**Feature Branch**: `001-list-enhancements`
**Created**: 2025-11-13
**Status**: Draft
**Input**: User description: "Let's expand the ability of lmk list:
- add the ability to specify a SQID to `lmk list` to only list a subtree
- add a flag to show extant doctypes in each node
- add a flag to show a list of relative paths to all files in each node

When each flag is enabled, it should display in both the regular text output or the JSON output."

## Clarifications

### Session 2025-11-13

- Q: How does the system handle nodes with no associated files/doctypes when display flags are enabled? → A: Show nothing (skip the metadata line entirely for that node)
- Q: How should metadata be displayed in tree text output format? → A: On separate indented lines below the node
- Q: What happens when a SQID exists in the file system but is not part of the current outline hierarchy? → A: Display the orphaned node only (with warning)
- Q: How should multiple doctypes be displayed when a node has more than one? → A: Display all as comma-separated list
- Q: How should very long file paths be handled in tree view display? → A: Display full paths without truncation (let terminal handle wrapping/scrolling)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Subtree Filtering by SQID (Priority: P1)

A user wants to focus on viewing only a specific branch of their outline hierarchy without being overwhelmed by the entire tree structure. They need to quickly navigate and understand a particular section of their documentation.

**Why this priority**: This provides the most fundamental navigation improvement, enabling users to scope their view to relevant sections. This is the foundation for efficient outline exploration in large projects.

**Independent Test**: Can be fully tested by running `lmk list <sqid>` and verifying that only the subtree rooted at that SQID is displayed, delivering focused navigation value.

**Acceptance Scenarios**:

1. **Given** an outline with multiple levels and a node with SQID "ABC123", **When** user runs `lmk list ABC123`, **Then** only the subtree starting from node "ABC123" and its descendants are displayed
2. **Given** an outline with a leaf node having SQID "XYZ789", **When** user runs `lmk list XYZ789`, **Then** only that single node is displayed with no children
3. **Given** an invalid SQID "INVALID", **When** user runs `lmk list INVALID`, **Then** an error message is displayed indicating the SQID does not exist
4. **Given** a SQID that exists in the filesystem but is not part of the current outline, **When** user runs `lmk list <orphaned-sqid>`, **Then** the orphaned node is displayed with a warning message

---

### User Story 2 - Display Doctypes in Outline (Priority: P2)

A user managing documentation with different doctypes (reports, specifications, guides) needs to see at a glance which doctype each node represents, enabling them to quickly identify document categories without opening each file.

**Why this priority**: This adds significant organizational value by surfacing metadata directly in the outline view, but the basic list functionality works without it.

**Independent Test**: Can be fully tested by running `lmk list --show-doctypes` and verifying that each node displays its associated doctype(s), delivering metadata visibility value.

**Acceptance Scenarios**:

1. **Given** nodes with various doctypes, **When** user runs `lmk list --show-doctypes`, **Then** each node displays its doctype on a separate indented line below the node in the tree view
2. **Given** the same outline, **When** user runs `lmk list --show-doctypes --json`, **Then** the JSON output includes a "doctypes" field for each node containing a list of extant doctypes
3. **Given** a node with no doctype assigned, **When** displayed with `--show-doctypes` flag, **Then** no doctype metadata line is shown for that node
4. **Given** a node with multiple doctypes, **When** user runs `lmk list --show-doctypes`, **Then** all doctypes are displayed as a comma-separated list on a single metadata line

---

### User Story 3 - Display File Paths in Outline (Priority: P3)

A user needs to understand which specific files are associated with each node in the outline, enabling them to quickly locate and access source files for editing or review.

**Why this priority**: While useful for advanced workflows, this is the least critical feature as users can typically infer file relationships from node structure. It provides convenience rather than essential functionality.

**Independent Test**: Can be fully tested by running `lmk list --show-files` and verifying that each node displays the relative paths to its associated files, delivering file location transparency.

**Acceptance Scenarios**:

1. **Given** nodes with associated markdown files, **When** user runs `lmk list --show-files`, **Then** each node displays relative file paths on separate indented lines below the node in the tree view
2. **Given** the same outline, **When** user runs `lmk list --show-files --json`, **Then** the JSON output includes a "files" field for each node containing a list of relative file paths
3. **Given** a node with multiple associated files, **When** displayed with `--show-files` flag, **Then** all relative paths are shown as a list
4. **Given** a node with very long file paths, **When** user runs `lmk list --show-files`, **Then** the full path is displayed without truncation

---

### User Story 4 - Combined Flags (Priority: P3)

A user wants comprehensive visibility into their outline structure by using multiple display flags simultaneously, seeing the full context of each node including its subtree, doctypes, and files.

**Why this priority**: This is a combination of other features rather than new functionality, providing comprehensive views for power users.

**Independent Test**: Can be fully tested by running `lmk list <sqid> --show-doctypes --show-files` and verifying all flags work together correctly, delivering complete outline metadata visibility.

**Acceptance Scenarios**:

1. **Given** an outline, **When** user runs `lmk list --show-doctypes --show-files`, **Then** both doctypes and file paths are displayed for each node in the tree view
2. **Given** the same outline, **When** user runs `lmk list ABC123 --show-doctypes --show-files --json`, **Then** JSON output includes only the subtree and each node has both "doctypes" and "files" fields
3. **Given** any combination of flags, **When** user switches between text and JSON output, **Then** all requested information is present in both output formats

---

### Edge Cases

- SQID exists in filesystem but not in current outline hierarchy: display the orphaned node only with a warning message
- Multiple doctypes assigned to a node: display all as comma-separated list in tree view; as array in JSON
- Very long file paths: display full paths without truncation; terminal handles wrapping/scrolling
- Nodes with no associated files/doctypes: metadata line is omitted entirely in tree view; JSON omits the field
- What happens when combining a subtree SQID that doesn't exist with display flags?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept an optional SQID argument to the `lmk list` command to filter the outline to a specific subtree
- **FR-002**: System MUST display only the node matching the provided SQID and all its descendants when a SQID is provided
- **FR-003**: System MUST display an error message when an invalid or non-existent SQID is provided
- **FR-003a**: System MUST display orphaned nodes (SQIDs that exist in filesystem but not in outline) with a warning message when requested
- **FR-004**: System MUST support a `--show-doctypes` flag that displays the extant doctypes for each node
- **FR-004a**: System MUST display multiple doctypes as a comma-separated list in tree text output
- **FR-005**: System MUST support a `--show-files` flag that displays relative file paths for each node
- **FR-005a**: System MUST display full file paths without truncation in tree text output regardless of length
- **FR-006**: System MUST display doctype and file information in both tree text output and JSON output when flags are enabled
- **FR-007**: System MUST allow multiple flags to be used simultaneously (e.g., both `--show-doctypes` and `--show-files`)
- **FR-008**: System MUST allow the SQID argument to be combined with display flags
- **FR-009**: System MUST maintain the existing tree structure formatting when displaying additional metadata
- **FR-009a**: System MUST display metadata (doctypes and file paths) on separate indented lines below each node in tree text output
- **FR-010**: System MUST include a "doctypes" field in JSON output containing a list of doctypes when `--show-doctypes` is enabled
- **FR-011**: System MUST include a "files" field in JSON output containing a list of relative file paths when `--show-files` is enabled
- **FR-012**: System MUST omit metadata fields in JSON output when a node has no associated data for that field
- **FR-013**: System MUST omit metadata lines in tree text output when a node has no associated data to display
- **FR-014**: System MUST preserve existing behavior when no SQID argument or flags are provided

### Assumptions

- Doctypes are already stored as metadata in the node/file structure
- File paths are relative to the outline root directory
- The existing JSON output structure can accommodate additional fields
- Tree formatting can accommodate additional metadata without becoming unreadable
- SQIDs are unique identifiers that can unambiguously identify nodes

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can filter the outline to any subtree in under 2 seconds by providing a SQID
- **SC-002**: Users can identify document types across an outline of 100+ nodes without opening any files
- **SC-003**: Users can locate source files for any node without navigating the file system manually
- **SC-004**: Combined flag usage (all features together) completes in under 3 seconds for outlines with 100 nodes
- **SC-005**: JSON output with all flags enabled remains parseable and includes all requested metadata fields
- **SC-006**: Tree text output with all flags enabled remains readable and properly formatted for outlines up to 50 nodes deep
