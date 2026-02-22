# REPEAT Pipeline

The REPEAT (Reproducible Evidence Pipeline with End-to-end Attestation of Tiles)
pipeline processes B4IU tiles in sequence, building a verifiable hash chain
that proves `compute = memory = identity`.

Entry point: `python -m tools.emit_run` to generate a run, then `make verify` to attest it.
