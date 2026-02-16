-include make/trtl.mk

.PHONY: test
test:
	pytest -v tests/
