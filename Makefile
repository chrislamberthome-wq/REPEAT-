# Verify REPEAT Receipt v1 contract compliance
.PHONY: verify-receipts
verify-receipts:
	pytest -q tests/test_repeat_receipt_contract.py

-include make/trtl.mk