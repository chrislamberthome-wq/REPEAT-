.PHONY: test lint format clean install build help

help:
	@echo "Available targets:"
	@echo "  make test     - Run tests with pytest"
	@echo "  make lint     - Run linters (ruff and mypy)"
	@echo "  make format   - Format code with ruff"
	@echo "  make clean    - Remove build artifacts"
	@echo "  make install  - Install package and dependencies"
	@echo "  make build    - Build package"

test:
	python -m pytest tests/ -v

lint:
	python -m ruff check .
	python -m mypy repeat_hd/ --ignore-missing-imports

format:
	python -m ruff check --fix .
	python -m ruff format .

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	pip install -e .[dev]

build:
	python -m build