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
	@python -m verifier.b4iu_snn_verify examples/b4iu_snn_v0.1_synthetic_run

.PHONY: emit-b4iu-snn-synth
emit-b4iu-snn-synth:
	@python -m tools.b4iu_snn_emit_synthetic_run examples/b4iu_snn_v0.1_synthetic_run

