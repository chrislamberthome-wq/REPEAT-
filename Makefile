# Makefile

# Other content of the Makefile... 

.PHONY: ci test-schema

test-schema:
	pytest -q tests/test_schema_validation.py

ci: test-schema test
