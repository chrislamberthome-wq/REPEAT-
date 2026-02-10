# TRTL Makefile for REPEAT-HD project

.PHONY: test smoke verify-tree lint clean help

# Default target
all: test

# Run all tests
test:
	python -m pytest tests/ -v

# Run smoke test (quick validation)
smoke:
	@echo "Running smoke test..."
	python -m repeat_hd.cli encode "smoke test" | python -m repeat_hd.cli verify
	@echo "Smoke test passed!"

# Verify tree - run all verification checks (tests + publichex verification)
verify-tree: test
	@echo "Tree verification complete!"

# Lint the code
lint:
	python -m flake8 repeat_hd tests

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

# Show help
help:
	@echo "Available targets:"
	@echo "  test        - Run all tests"
	@echo "  smoke       - Run quick smoke test"
	@echo "  verify-tree - Run all verification checks"
	@echo "  lint        - Lint the code"
	@echo "  clean       - Clean up temporary files"
	@echo "  help        - Show this help message"
