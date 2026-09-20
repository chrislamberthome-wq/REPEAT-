.PHONY: all clean install test ci-count-b4iu diag-strict diag-boundary diag-core-index diag-governance

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

diag-boundary:
	@test -f schemas/CORE_INDEX.v1.json
	@test -f docs/boundary-authority-v1.md
	@test -f audits/2026-09-20_repeat-core-boundary-audit.md
	@echo "Boundary artifacts: present."

diag-core-index:
	python3 tools/validate_core_index.py

diag-governance: diag-boundary diag-core-index diag-strict
	@echo "Diagnostics (governance) passed."

diag-strict:
	python -m verifier --help > /dev/null
	@echo "verifier entrypoint: OK"
	python3 simulate_mram_runs.py --mode pass --seed 42 --output /tmp/diag_receipts.jsonl
	python -m verifier /tmp/diag_receipts.jsonl
	@echo "Diagnostics (strict) passed."
