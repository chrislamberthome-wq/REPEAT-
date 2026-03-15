# Makefile

# Other content of the Makefile... 

.PHONY: ci test-schema verify-example

test-schema:
	pytest -q tests/test_schema_validation.py

ci: test-schema test

verify-example:
	python -m verifier tests/vectors/repo_reference/valid_minimal.json
