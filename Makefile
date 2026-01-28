# Makefile

fmt:
	ruff format .

lint:
	ruff check .

type:
	mypy tron_repeat

test:
	pytest -q

ci:
	$(MAKE) lint
	$(MAKE) type
	$(MAKE) test
