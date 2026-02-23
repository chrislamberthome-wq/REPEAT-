# Makefile for REPEAT-

# Targets
.PHONY: all clean install test ci-count-b4iu diag-strict

all: install

install:
	@echo "Running installation..."

clean:
	@echo "Cleaning up..."

# Run the test suite (fail-closed: non-zero exit propagated by pytest)
test:
	pytest tests/

# B4IU locked counter check.
# If scripts/count_b4iu.py exists, run it and propagate its exit code (fail-closed).
# If it does not exist, print an informational notice — this avoids a silent no-op
# that would mask missing enforcement if the script is later added.
ci-count-b4iu:
	@if [ -f scripts/count_b4iu.py ]; then \
		python scripts/count_b4iu.py; \
	else \
		echo "NOTICE: scripts/count_b4iu.py not found — B4IU counter not enforced"; \
	fi

# Strict diagnostics: generate sample receipts, then run the canonical verifier
# (fail-closed), plus flake8 hard-error checks.
diag-strict:
	python3 simulate_mram_runs.py --mode pass --seed 42 --output /tmp/diag_receipts_pass.jsonl
	python -m verifier /tmp/diag_receipts_pass.jsonl
	python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output /tmp/diag_receipts_drift.jsonl
	python -m verifier /tmp/diag_receipts_drift.jsonl
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

