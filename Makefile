# Optional include of the repo build system
-include make/trtl.mk

.PHONY: constraints-lint
constraints-lint:
	python tools/constraints_lint.py constraints.md

.PHONY: claim-ledger-lint
claim-ledger-lint:
	python tools/claim_ledger_lint.py governance/claim_ledger.v1.jsonl

.PHONY: uc
uc: constraints-lint claim-ledger-lint
	@echo "UC: OK"