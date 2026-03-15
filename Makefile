.PHONY: test-schema ci

test-schema:
	python scripts/validate_repo_reference.py \
		schemas/repo-reference.schema.json \
		examples/repo-reference.valid.json
	python scripts/validate_repo_reference.py \
		schemas/repo-reference.schema.json \
		examples/repo-reference.invalid.json; test $$? -eq 1

ci: test test-schema

