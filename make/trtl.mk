# TRTL Makefile - Test, Run Tests, and Lint
#
# This Makefile provides standard targets for testing, linting, and verification.

.PHONY: test smoke verify-tree lint

# Run all tests
test:
	python -m pytest tests/ -v

# Run smoke test (quick validation)
smoke:
	@echo "Running smoke test..."
	@python -m repeat_hd.cli encode "smoke test data" | python -m repeat_hd.cli verify --strict
	@echo "Smoke test passed!"

# Verify tree - comprehensive validation for CI gating
verify-tree: lint test
	@echo "All verification checks passed!"

# Run linters
lint:
	@echo "Running linters..."
	python -m flake8 repeat_hd/ tests/ --max-line-length=100 --ignore=E501,W503,W293,F401
	@echo "Linting passed!"
