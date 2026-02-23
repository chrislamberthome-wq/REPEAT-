# Makefile for REPEAT-

.PHONY: all clean install simulate test verify ci-count-b4iu ci

all: install

install:
	@echo "Running installation..."

clean:
	@echo "Cleaning up..."
	rm -f mram_receipts.jsonl

simulate:
	python3 simulate_mram_runs.py --mode pass --seed 42 --output mram_receipts.jsonl

test:
	pytest tests/ -v

verify: simulate
	python -m verifier mram_receipts.jsonl

ci-count-b4iu:
	@python3 -c "\
import sys, os; \
f = 'mram_receipts.jsonl'; \
sys.exit(1) if not os.path.exists(f) else None; \
fh = open(f); c = sum(1 for l in fh if l.strip()); fh.close(); \
sys.exit(0 if c else 1)"
	@echo "B4IU receipts: OK"

ci: verify test ci-count-b4iu
	@echo "CI complete (fail-closed)."

