# Quickstart: Enhanced List Command Implementation

**Feature**: 001-list-enhancements
**Date**: 2025-11-13
**For**: Developers implementing this feature

## Overview

This guide provides a step-by-step implementation path for the enhanced `lmk list` command. Follow these steps in order, writing tests first for each component (TDD workflow).

---

## Prerequisites

- Completed specification ([spec.md](./spec.md))
- Completed research ([research.md](./research.md))
- Completed data model ([data-model.md](./data-model.md))
- Completed contracts ([contracts/list_command.md](./contracts/list_command.md))
- Development environment set up with:
  - Python 3.13+
  - uv for dependency management
  - pytest, mypy, ruff installed

---

## Implementation Steps

### Step 1: Extend ListOutlineUseCase (Use Case Layer)

**File**: `src/linemark/use_cases/list_outline.py`

**Changes**:
1. Add optional `root_sqid` parameter to `execute()` method
2. Implement `_filter_to_subtree()` private method
3. Implement `_is_orphaned()` private method
4. Implement `_get_subtree()` private method

**Test First** (`tests/unit/test_list_outline_use_case.py`):
```python
def test_execute_with_valid_sqid_filters_to_subtree()
def test_execute_with_leaf_sqid_returns_single_node()
def test_execute_with_invalid_sqid_raises_error()
def test_execute_with_orphaned_sqid_returns_node_only()
def test_execute_without_sqid_returns_all_nodes()  # Backward compatibility
```

**Implementation Pattern**:
```python
def execute(self, directory: Path, root_sqid: str | None = None) -> list[Node]:
    """Execute the list outline use case.

    Args:
        directory: Working directory containing outline files
        root_sqid: Optional SQID to filter to subtree

    Returns:
        List of nodes (all or filtered subtree)

    Raises:
        ValueError: If root_sqid is invalid or not found
    """
    # Load all nodes (existing logic)
    all_nodes = self._load_all_nodes(directory)

    # Filter if requested
    if root_sqid:
        return self._filter_to_subtree(all_nodes, root_sqid)

    return all_nodes
```

**Key Points**:
- Maintain existing behavior when `root_sqid=None`
- Use materialized path prefix matching for descendants
- Handle orphaned nodes gracefully (return just the node)
- Raise `ValueError` for truly invalid/missing SQIDs

---

### Step 2: Extend Formatters (Presentation Layer)

**File**: `src/linemark/cli/formatters.py`

**Changes**:
1. Add optional parameters to `format_tree()`:
   - `show_doctypes: bool = False`
   - `show_files: bool = False`
   - `directory: Path | None = None`

2. Add optional parameters to `format_json()`:
   - `show_doctypes: bool = False`
   - `show_files: bool = False`
   - `directory: Path | None = None`

**Test First** (`tests/unit/test_formatters.py` - create new file):
```python
# Tree formatting
def test_format_tree_with_show_doctypes()
def test_format_tree_with_show_files()
def test_format_tree_with_both_flags()
def test_format_tree_without_flags()  # Backward compatibility
def test_format_tree_omits_empty_metadata()
def test_format_tree_formats_multiple_doctypes()

# JSON formatting
def test_format_json_with_show_doctypes()
def test_format_json_with_show_files()
def test_format_json_with_both_flags()
def test_format_json_without_flags()  # Backward compatibility
def test_format_json_omits_empty_metadata_fields()
```

**Implementation Pattern for `format_tree()`**:
```python
def format_tree(
    nodes: list[Node],
    show_doctypes: bool = False,
    show_files: bool = False,
    directory: Path | None = None,
) -> str:
    """Format nodes as a tree with optional metadata.

    Args:
        nodes: List of nodes sorted by materialized path
        show_doctypes: Whether to display document types
        show_files: Whether to display file paths
        directory: Base directory for relative paths (required if show_files=True)

    Returns:
        Tree-formatted string
    """
    if not nodes:
        return ''

    lines: list[str] = []

    for node in nodes:
        # Add node line (existing logic)
        lines.append(_format_node_line(node, nodes))

        # Add metadata lines if requested
        if show_doctypes and node.document_types:
            lines.extend(_format_doctypes_lines(node, nodes))

        if show_files and node.document_types:
            lines.extend(_format_files_lines(node, nodes, directory))

    return '\n'.join(lines)
```

**Key Points**:
- Metadata lines use proper tree connectors (`├─`, `└─`)
- Indentation matches the node's tree level
- Empty metadata is omitted entirely
- Backward compatible (defaults maintain current output)

---

### Step 3: Update CLI Command (CLI Layer)

**File**: `src/linemark/cli/main.py`

**Changes**:
1. Modify `@lmk.command()` decorator for `list()` function:
   - Add `@click.argument('sqid', required=False)`
   - Add `@click.option('--show-doctypes', is_flag=True, ...)`
   - Add `@click.option('--show-files', is_flag=True, ...)`

2. Update function signature and body to pass new parameters through

**Test First** (`tests/integration/test_list_command_integration.py` - create new file):
```python
def test_list_command_without_args()  # Backward compatibility
def test_list_command_with_sqid()
def test_list_command_with_show_doctypes()
def test_list_command_with_show_files()
def test_list_command_with_all_flags_combined()
def test_list_command_with_invalid_sqid()
def test_list_command_with_orphaned_sqid()
def test_list_command_json_output()
def test_list_command_json_with_metadata()
```

**Implementation Pattern**:
```python
@lmk.command()
@click.argument('sqid', required=False, type=str)
@click.option(
    '--show-doctypes',
    is_flag=True,
    default=False,
    help='Display document types for each node',
)
@click.option(
    '--show-files',
    is_flag=True,
    default=False,
    help='Display file paths for each node',
)
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.option(
    '-d',
    '--directory',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help='Working directory',
)
def list(
    sqid: str | None,
    show_doctypes: bool,
    show_files: bool,
    output_json: bool,
    directory: Path,
) -> None:  # noqa: A001
    """List all nodes in the outline, optionally filtered to a subtree.

    Examples:
        # Show full outline
        lmk list

        # Show subtree starting at SQID
        lmk list A3F7c

        # Show with document types
        lmk list --show-doctypes

        # Show with file paths
        lmk list --show-files

        # Combine all options
        lmk list A3F7c --show-doctypes --show-files --json
    """
    try:
        # Create adapter
        filesystem = FileSystemAdapter()

        # Execute use case
        use_case = ListOutlineUseCase(filesystem=filesystem)
        nodes = use_case.execute(directory=directory, root_sqid=sqid)

        # Format and output
        if output_json:
            output = format_json(
                nodes,
                show_doctypes=show_doctypes,
                show_files=show_files,
                directory=directory,
            )
        else:
            output = format_tree(
                nodes,
                show_doctypes=show_doctypes,
                show_files=show_files,
                directory=directory,
            )

        if output:
            click.echo(output)
        else:
            click.echo('No nodes found in outline.', err=True)

    except ValueError as e:
        click.echo(f'Error: {e}', err=True)
        sys.exit(1)
```

**Key Points**:
- Argument order: SQID before options (Click convention)
- All new options default to False (backward compatibility)
- Pass directory to formatters for file path computation
- Handle orphan warnings in use case, not CLI (separation of concerns)

---

### Step 4: Manual Testing Checklist

After implementing and passing all automated tests:

1. **Basic Functionality**:
   ```bash
   lmk list                           # Full outline
   lmk list VALID_SQID                # Subtree
   lmk list --json                    # JSON output
   ```

2. **Metadata Display**:
   ```bash
   lmk list --show-doctypes           # Doctypes only
   lmk list --show-files              # Files only
   lmk list --show-doctypes --show-files  # Both
   ```

3. **Combinations**:
   ```bash
   lmk list SQID --show-doctypes --show-files --json
   ```

4. **Error Cases**:
   ```bash
   lmk list INVALID                   # Should error
   lmk list ORPHAN                    # Should warn but succeed
   ```

5. **Performance** (with 100-node test outline):
   ```bash
   time lmk list
   time lmk list SQID
   time lmk list --show-doctypes --show-files
   ```
   All should complete under 3 seconds.

---

## TDD Workflow

For each step above, follow this cycle:

### Red Phase
1. Write failing test(s) for the new functionality
2. Run tests: `pytest tests/unit/test_file.py::test_name -v`
3. Confirm test fails with expected failure message

### Green Phase
1. Implement minimal code to make test pass
2. Run tests again
3. Confirm test passes

### Refactor Phase
1. Clean up implementation
2. Run full test suite: `./scripts/runtests.sh`
3. Ensure 100% coverage maintained
4. Run quality checks:
   ```bash
   uv run ruff format
   uv run ruff check --fix --unsafe-fixes
   uv run mypy src/
   ```

### Integration
1. Run integration tests: `pytest tests/integration/`
2. Manual smoke testing with real outline
3. Verify backward compatibility (existing usage unchanged)

---

## Common Pitfalls

### 1. Modifying Domain Entities

**Wrong**:
```python
# DON'T add display logic to Node
class Node:
    def format_doctypes(self) -> str:
        return ", ".join(sorted(self.document_types))
```

**Right**:
```python
# DO keep formatting in presentation layer
def _format_doctypes_string(node: Node) -> str:
    return ", ".join(sorted(node.document_types))
```

---

### 2. Breaking Backward Compatibility

**Wrong**:
```python
# DON'T change existing defaults
def format_tree(nodes: list[Node], show_doctypes: bool = True):
    # This breaks existing callers!
```

**Right**:
```python
# DO default to False (existing behavior)
def format_tree(nodes: list[Node], show_doctypes: bool = False):
    # Existing callers get same output
```

---

### 3. Ignoring Empty Metadata

**Wrong**:
```python
# DON'T show empty metadata lines
if show_doctypes:
    lines.append(f"├─ doctypes: {doctypes or 'none'}")
```

**Right**:
```python
# DO omit metadata when empty
if show_doctypes and node.document_types:
    lines.append(f"├─ doctypes: {doctypes}")
```

---

### 4. Incorrect Tree Indentation

**Wrong**:
```python
# DON'T use fixed indentation for metadata
lines.append("  ├─ doctypes: draft, notes")
```

**Right**:
```python
# DO compute indentation based on node depth
prefix = _build_prefix(node, all_nodes)
lines.append(f"{prefix}├─ doctypes: draft, notes")
```

---

## Quality Gates

Before considering this feature complete:

- [ ] All unit tests pass (`pytest tests/unit/`)
- [ ] All integration tests pass (`pytest tests/integration/`)
- [ ] 100% test coverage (`pytest --cov=linemark --cov-report=term-missing`)
- [ ] mypy strict mode passes (`uv run mypy src/`)
- [ ] ruff linting passes (`uv run ruff check src/ tests/`)
- [ ] Code formatted (`uv run ruff format src/ tests/`)
- [ ] Manual testing checklist completed
- [ ] Performance targets met (< 3 seconds for 100 nodes)
- [ ] Backward compatibility verified (existing usage unchanged)

---

## Getting Help

- **Specification Questions**: Review [spec.md](./spec.md) and clarifications
- **Design Questions**: Review [data-model.md](./data-model.md) and [research.md](./research.md)
- **Contract Questions**: Review [contracts/list_command.md](./contracts/list_command.md)
- **Implementation Questions**: Check existing similar code (e.g., `format_tree()` current implementation)

---

## Next Steps

After completing this feature:

1. Run full test suite one final time
2. Commit changes with descriptive message
3. Create pull request linking to specification
4. Update CLAUDE.md if new patterns were established
5. Consider creating user documentation/examples

---

## Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Step 1 | 2-3 hours | Extend use case with subtree filtering |
| Step 2 | 3-4 hours | Enhance formatters with metadata display |
| Step 3 | 1-2 hours | Update CLI command interface |
| Step 4 | 1 hour | Manual testing and verification |
| **Total** | **7-10 hours** | Complete feature implementation |

Times include test writing, implementation, and refactoring per TDD workflow.
