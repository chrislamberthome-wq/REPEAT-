.PHONY: test diag-strict lint clean

test:
	python -m pytest tests/ -v

diag-strict:
	python -m pytest tests/ -v --tb=short

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

-include make/trtl.mk
