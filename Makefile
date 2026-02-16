-include make/trtl.mk

.PHONY: test
test:
	python -m pytest tests/ -v