# Clean build artifacts
clean:
	rm -rf dist/

# Build the package
build: clean
	uv build

# Publish the package
publish: build
	uv publish
