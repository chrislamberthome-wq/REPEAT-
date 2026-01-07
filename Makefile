.PHONY: test smoke verify-tree

test:
	pytest -q

smoke:
	python -m repeat_hd.cli encode "hello" > ./repeat_hd_frame.bin
	python -m repeat_hd.cli verify --infile ./repeat_hd_frame.bin
	rm -f ./repeat_hd_frame.bin

verify-tree:
	@if git check-ignore -v repeat_hd tests; then \
		echo "ERROR: repeat_hd/ or tests/ are ignored by .gitignore"; \
		exit 1; \
	fi
	test -d repeat_hd
	test -d tests
	test -d .github/workflows
