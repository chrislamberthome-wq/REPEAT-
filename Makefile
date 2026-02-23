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

# Locked B4IU occurrence counter.
# The count is computed over normative spec/doc files only.
# Update EXPECTED_B4IU if the normative spec intentionally changes.
EXPECTED_B4IU := 1
ci-count-b4iu:
	@echo "Counting B4IU references in normative spec files..."
	@count=$$(grep -rc "B4IU" SPEC.md C14N_RULES.md formulas.md 2>/dev/null | \
	         awk -F: '{s+=$$2} END {print s+0}'); \
	 echo "B4IU count: $$count (expected: $(EXPECTED_B4IU))"; \
	 if [ "$$count" -ne "$(EXPECTED_B4IU)" ]; then \
	   echo "ERROR: B4IU count mismatch — expected $(EXPECTED_B4IU), got $$count" >&2; \
	   exit 1; \
	 fi
	@echo "B4IU counter OK"

# Strict diagnostics: run claim-ledger lint; fail on any error.
diag-strict:
	python tools/claim_ledger_lint.py --strict

