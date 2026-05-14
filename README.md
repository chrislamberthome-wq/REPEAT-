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

## blood-ion-repeat — ionic channel multi-trial replay and verification

The `blood_ion_repeat` package implements multi-trial replay and auditable
verification for ionic-channel experiments (e.g. saline or hydrogel substrates).

### Module layout

```
blood_ion_repeat/
├── __init__.py
├── replay.py        # TrialVerifyRecord, ReplaySummary, trial-grouping logic
└── verify_run.py    # config/trace validation, receipt builder, CLI entrypoint
schemas/
└── verification_receipt.schema.json   # JSON Schema for verification receipts
examples/
├── config_hydrogel_baseline.json      # Hydrogel baseline experiment config
├── config_saline_noisy.json           # Noisy saline experiment config
└── sample_trace_multitrial.jsonl      # Multi-trial example trace (3 trials × 12 symbols)
```

### Verification receipt fields

| Field | Description |
|---|---|
| `trial_count` | Total number of trials observed in the trace |
| `trials_passed` | Trials with zero symbol errors and CRC match |
| `trials_failed` | Trials that failed |
| `aggregate_ber` | `total_symbol_errors / total_symbols` across all trials |
| `crc_pass_rate` | Fraction of trials where CRC-16/CCITT-FALSE matched |
| `sha256_trace` | SHA-256 fingerprint of the canonical trace |
| `trial_results` | Per-trial list with `trial_index`, `ber`, `crc_pass`, `passed`, `fail_reason` |

### Single-trial verification

Verify a trace using one of the provided configs and print the receipt to stdout:

```bash
python -m blood_ion_repeat.verify_run \
    examples/config_hydrogel_baseline.json \
    examples/sample_trace_multitrial.jsonl
```

Or via Make:

```bash
make verify-single
```

### Multi-trial verification (save receipt to file)

```bash
python -m blood_ion_repeat.verify_run \
    examples/config_hydrogel_baseline.json \
    examples/sample_trace_multitrial.jsonl \
    --output /tmp/multitrial_receipt.json
```

Or via Make:

```bash
make verify-multi
```

The command exits with:
- `0` — all trials passed
- `1` — one or more trials failed
- `2` — configuration or trace validation error