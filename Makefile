# Makefile for REPEAT-

# Targets
.PHONY: all clean install test ci-count-b4iu diag-strict

all: install

install: 
	@echo "Running installation..."

clean:
	@echo "Cleaning up..."

test:
	pytest tests/

ci-count-b4iu:
	@echo "B4IU locked counter: checking for B4IU references..."
	@grep -r "B4IU" --include="*.md" --include="*.py" --include="*.json" . | wc -l | xargs echo "B4IU references:"

diag-strict:
	python -m verifier --help > /dev/null && echo "verifier entrypoint: OK"
	@echo "Diagnostics (strict) passed."

