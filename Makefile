# Optional include
-include make/trtl.mk

.PHONY: claim-ledger-lint
claim-ledger-lint:
	@echo "Linting the claim ledger..."
	python tools/claim_ledger_lint.py governance/claim_ledger.v1.jsonl

.PHONY: uc
uc: constraints-lint claim-ledger-lint
	@echo "UC: OK"