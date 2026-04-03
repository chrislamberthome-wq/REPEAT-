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

## Blood-Ion-Repeat: Ionic Channel Communication Experiments

The `blood_ion_repeat/` package provides a simulation framework for ionic
channel communication using a blood-analog substrate (saline / saline hydrogel).

### Package structure

```
blood_ion_repeat/
├── __init__.py
├── canonical.py       — deterministic JSON serialisation for hashing
├── crc16.py           — CRC-16/CCITT-FALSE implementation
├── receipt.py         — summary receipt builder
├── trace.py           — JSONL trace writer / reader
├── thresholds.py      — pre-registered decoding threshold logic
├── channel_model.py   — ionic channel simulation + params_for_trial()
├── verifier.py        — authoritative verifier (verify_run.py)
└── run_experiment.py  — multi-trial trace generator (provisional receipts)
```

### Running a multi-trial experiment

`run_experiment.py` is a **trace generator** and **provisional receipt emitter**.
It is *not* the authoritative verifier.

```bash
make run-multitrial
```

or manually:

```bash
python -m blood_ion_repeat.run_experiment \
    --config examples/config_saline_multitrial.json \
    --trace /tmp/saline_multitrial.jsonl \
    --receipt /tmp/saline_multitrial_provisional.json \
    --seed 42
```

### Verifying a multi-trial trace

`verify_run.py` (backed by `blood_ion_repeat.verifier`) is the **authoritative
verifier**.  Always use this for audit or publication purposes.

```bash
make verify-multitrial
```

or manually:

```bash
python verify_run.py /tmp/saline_multitrial.jsonl \
    --config examples/config_saline_multitrial.json \
    --receipt /tmp/saline_multitrial_authoritative.json
```

### Multi-trial configuration fields

| Field | Type | Default | Description |
|---|---|---|---|
| `trials` | integer | — | Number of trials to execute |
| `timestamp_seed_utc` | ISO-8601 string | (wall clock) | Base time for deterministic timestamps |
| `trial_spacing_seconds` | number | 60 | Simulated seconds between trial starts |
| `symbol_spacing_seconds` | number | 1 | Simulated seconds between symbols within a trial |
| `noise_schedule_mv` | array of numbers | (channel default) | Per-trial noise offset (mV); last value repeated if shorter than trials |

### Per-trial noise schedules

`channel_model.params_for_trial(base, trial_index, noise_schedule_mv)` returns
adjusted channel parameters for each trial.  A negative schedule value reduces
noise (higher SNR); a positive value increases it.  Noise is clamped to ≥ 0.

Example (`examples/config_saline_multitrial.json`):

```json
{
  "trials": 3,
  "timestamp_seed_utc": "2026-04-02T12:00:00Z",
  "noise_schedule_mv": [0.0, -10.0, -30.0]
}
```

Trial 0 uses the default noise level; trial 1 reduces it by 10 mV; trial 2
reduces it by 30 mV (near-zero noise, highest SNR).