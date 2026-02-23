# Makefile for REPEAT-

# Targets
.PHONY: all clean install test ci-count-b4iu diag-strict

all: install

install: 
	@echo "Running installation..."

clean:
	@echo "Cleaning up..."

test:
	python -m pytest tests/ -v

ci-count-b4iu:
	@echo "Counting B4IU occurrences..."
	@grep -r "B4IU" --include="*.md" --include="*.py" --include="*.txt" . | wc -l

diag-strict:
	@echo "Running strict diagnostics..."
	python -m pytest tests/ -v --tb=short

