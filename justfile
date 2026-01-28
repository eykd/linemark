# Clean build artifacts
clean:
	rm -rf dist/

# Build the package
build: clean
	uv build

# Publish the package
publish: build
	uv publish

# Run pre-commit hooks on all files
lint:
	uv run pre-commit run --all-files

# Run all CI checks (format, lint, type check, tests)
ci:
	uv run ruff format --check
	uv run ruff check
	uv run mypy src tests
	uv run pytest

# Auto-fix formatting and linting issues
fix:
	uv run ruff format
	uv run ruff check --fix

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=linemark --cov-report=term-missing
