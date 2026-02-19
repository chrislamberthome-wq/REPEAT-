.PHONY: help test lint fmt ci

help:
	@printf "Targets: test lint fmt ci\n"

test:
	python -m pytest -q

lint:
	python -m compileall -q .

fmt:
	@printf "No formatter configured (stub).\n"

ci: test lint