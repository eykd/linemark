# Clean build artifacts
clean:
	rm -rf dist/

# Build the package
build: clean
	uv build

# Publish the package
publish: build
	uv publish

# Run ruff format and check
lint:
	uv run ruff format
	uv run ruff check --fix

# Run all pre-commit hooks on all files
pre-commit:
	uv run pre-commit run --all-files

# Run all CI checks (format check, lint, type check, tests)
ci:
	uv run ruff format --check
	uv run ruff check
	uv run mypy src tests
	uv run pytest --cov=linemark --cov-report=term-missing

# Run tests with coverage
test:
	uv run pytest --cov=linemark --cov-report=term-missing
