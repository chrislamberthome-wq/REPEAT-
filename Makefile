.PHONY: all clean install test ci-count-b4iu diag-strict run-multitrial verify-multitrial

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

run-multitrial:
	python -m blood_ion_repeat.run_experiment \
		--config examples/config_saline_multitrial.json \
		--trace /tmp/saline_multitrial.jsonl \
		--receipt /tmp/saline_multitrial_provisional.json \
		--seed 42
	@echo "Multi-trial trace: /tmp/saline_multitrial.jsonl"
	@echo "Provisional receipt: /tmp/saline_multitrial_provisional.json"

verify-multitrial:
	python verify_run.py /tmp/saline_multitrial.jsonl \
		--config examples/config_saline_multitrial.json \
		--receipt /tmp/saline_multitrial_authoritative.json
	@echo "Authoritative receipt: /tmp/saline_multitrial_authoritative.json"