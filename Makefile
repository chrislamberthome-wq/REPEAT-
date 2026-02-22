# Makefile for REPEAT-

# Targets
.PHONY: all clean install

all: install

install: 
	@echo "Running installation..."

clean:
	@echo "Cleaning up..."

.PHONY: verify
verify:
	@python -m verifier.verify

.PHONY: ci-count-b4iu
ci-count-b4iu: verify

