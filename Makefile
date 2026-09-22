.PHONY: all clean install test ci-count-b4iu diag-strict preservation-test

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
	python -m verifier --help > /dev/null
	@echo "verifier entrypoint: OK"
	python3 simulate_mram_runs.py --mode pass --seed 42 --output /tmp/diag_receipts.jsonl
	python -m verifier /tmp/diag_receipts.jsonl
	@echo "Diagnostics (strict) passed."

preservation-test:
	@python3 scripts/validate_preservation.py .
