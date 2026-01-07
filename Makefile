.PHONY: test smoke verify-tree

test:
	pytest -q

smoke:
	@set -e; \
	tmp_file="./repeat_hd_frame.bin"; \
	trap 'rm -f "$$tmp_file"' EXIT; \
	python -m repeat_hd.cli encode "hello" > "$$tmp_file"; \
	python -m repeat_hd.cli verify --infile "$$tmp_file"

verify-tree:
	@if git check-ignore -v repeat_hd tests; then \
		echo "ERROR: repeat_hd/ or tests/ are ignored by .gitignore"; \
		exit 1; \
	fi
	test -d repeat_hd
	test -d tests
	test -d .github/workflows
