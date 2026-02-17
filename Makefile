-include make/trtl.mk

.PHONY: ci-count-b4iu
ci-count-b4iu:
	node tools/ci/count_b4iu_locked.mjs

.PHONY: test
test:
	pytest -v