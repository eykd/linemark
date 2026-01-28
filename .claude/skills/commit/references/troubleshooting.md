# Commit Troubleshooting

## PostToolUse Hook Failures

The project uses PostToolUse hooks that run after Edit/Write operations. These hooks validate code quality before you commit.

### Ruff Format Errors

```bash
# Check what needs formatting
uv run ruff format --check

# Auto-fix formatting issues
uv run ruff format .
```

### Ruff Lint Errors

```bash
# Check for linting issues
uv run ruff check

# Auto-fix many linting issues
uv run ruff check --fix

# For complex issues, manually fix and retry
```

### Mypy Type Errors

```bash
# Check types
uv run mypy src tests

# Fix type errors manually
# Common fixes:
# - Add type annotations
# - Use proper generic types
# - Handle Optional values correctly
```

### Test Failures

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_module.py

# Run with coverage
uv run pytest --cov

# Fix failing tests and retry commit
```

## Commit Message Validation

### Common Line Length Errors

**Error: Line too long**

One or more lines exceed 100 characters (if using commitlint or similar).

Fix: Manually wrap long lines at natural break points:

```bash
# Before (fails)
git commit -m "feat: add feature

This is a very long line that exceeds one hundred characters and will cause the commit to fail."

# After (passes)
git commit -m "feat: add feature

This is a very long line that exceeds one hundred characters and
will cause the commit to fail."
```

**Other validation rules:**

- Ensure commit message follows conventional commit format
- Check that type is valid (feat, fix, docs, etc.)
- Subject line should be lowercase (after type:)
- No period at end of subject line
- Subject line max 100 characters

## Python Project Commit Scenarios

### New Feature with Tests

```
feat: add [feature name]

- Implement [component/function]
- Add comprehensive test coverage
- Update type annotations
```

### Bug Fix

```
fix: resolve [issue description]

- Fix [specific problem]
- Add regression test
```

### Configuration Changes

```
chore: update [tool] configuration

- Adjust [setting] for [reason]
- Impact: [description]
```

### Dependency Updates

```
chore: update dependencies

- Update [package] to v[version]
- Reason: [security/feature/bugfix]
```

### Refactoring

```
refactor: restructure [component]

- Extract [functionality] into separate module
- Improve [aspect] without changing behavior
- All tests pass
```

### Documentation

```
docs: update [documentation type]

- Add [section/topic]
- Clarify [concept]
```

## Environment Issues

### Missing Dependencies

If hooks fail because tools aren't installed:

```bash
# Install dev dependencies
uv sync --group dev

# Install test dependencies (includes ruff, mypy)
uv sync --group test

# Install all dependencies
uv sync --all-groups
```

### Git Hook Configuration

This project uses PostToolUse hooks (Claude Code feature), not git pre-commit hooks.

To check hook configuration:

```bash
cat .claude/settings.json
```

## Recovery from Failed Commits

**CRITICAL**: Always create NEW commits after failures, never amend:

```bash
# ❌ Wrong - this modifies the PREVIOUS commit
git add file.py
git commit --amend

# ✅ Correct - creates a NEW commit
git add file.py
git commit -m "fix: correct issue from previous attempt

- Address [specific problem]
- All validation passes"
```

**Why**: After a hook failure, the commit did NOT happen. Using `--amend` would modify the previous successful commit, potentially losing work.
