# ABOUTME: Build and development targets for reka-cli
# ABOUTME: Provides install, test, build, and release commands

.PHONY: install test test-integration build clean release

install:
	uv sync --extra dev

test:
	uv run pytest reka/tests/ -v -m "not integration"

test-integration:
	uv run pytest reka/tests/ -v -m integration

build:
	uv run pyinstaller --onefile --name reka reka/main.py

clean:
	rm -rf dist/ build/ *.spec __pycache__ .pytest_cache

release:
	@if [ -z "$(VERSION)" ]; then echo "Usage: make release VERSION=v0.1.0"; exit 1; fi
	git tag $(VERSION)
	git push origin $(VERSION)
