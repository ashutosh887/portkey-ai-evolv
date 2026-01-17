.PHONY: install dev test lint format type-check run-api run-cli init-db clean

# Install dependencies
install:
	uv sync

# Install with dev dependencies
dev:
	uv sync --dev

# Run tests
test:
	uv run pytest

# Lint code
lint:
	uv run ruff check .

# Format code
format:
	uv run black .

# Type check
type-check:
	uv run mypy .

# Run API server
run-api:
	uv run uvicorn apps.api.main:app --reload

# Run CLI
run-cli:
	uv run genome --help

# Initialize database
init-db:
	uv run python scripts/init_db.py

# Clean generated files
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf dist build *.egg-info
