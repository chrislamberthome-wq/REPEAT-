    # SOLID-FSK v0.1

Geometric resonance communication experiment using the five Platonic solids as spectral carriers.

Goal: encode a binary frame by exciting a physical solid and decoding from its resonant spectrum.

This implementation includes:
- CRC16 verification
- peak extraction from recorded audio
- template-based classifier
- deterministic JSONL audit traces

Status: experimental research protocol.

## Layout

SPEC_SOLID_FSK_v0_1.md — protocol specification  
schema/ — JSON schema for audit traces  
tools/ — signal processing + decoding tools  
tests/ — verification tests  
golden/ — calibration recordings + peak templates

## Quick test

Run tests:

```bash
pytest
```

---

## delta_repeat_proof_v1

A verifiable execution primitive that proves a governed decision occurred, execution followed constraints, the result is reproducible, and verification is independent.

```bash
git clone https://github.com/chrislamberthome-wq/REPEAT-
cd REPEAT-/delta_repeat_proof_v1
python verifier/verify.py
```