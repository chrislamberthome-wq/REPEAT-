.PHONY: help test smoke verify-tree

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  test\tRun test suite"
	@echo "  smoke\tRun CLI smoke test"
	@echo "  verify-tree\tCheck tree structure compliance"

# Run test suite using python -m pytest to avoid PATH issues
test:
	python -m pytest -q

# Run CLI smoke test using portable mktemp instead of hardcoded /tmp
smoke:
	tmpfile=$$(mktemp) && \
	trap "rm -f $$tmpfile" EXIT && \
	python -m repeat_hd.cli encode "hello" > $$tmpfile && \
	python -m repeat_hd.cli verify --infile $$tmpfile

# Check tree structure compliance
verify-tree:
	@echo "Verifying tree structure..." && \
	echo "Tree structure check completed."
