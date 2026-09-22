# Standalone V0.1 prototype

This is deliberately outside `REPEAT_CORE`. It uses only Python's standard library and operates on an exported JSONL artifact, so replay can happen on an ordinary laptop with the sensor disconnected.

## Capture

For the first bench run, acquire samples from the ADXL345 using the small SBC-specific adapter or export the sensor's samples as JSONL with the fields used by `capture`. The artifact format is intentionally local to this prototype and is **not** a REPEAT_CORE schema.

```bash
python prototype/evidence_node_v01.py capture \
  --input samples.jsonl \
  --output run/observations.jsonl \
  --device-id bench-0001 \
  --config-id vibration-100hz-v01 \
  --operator-mark 3.0,7.0
```

Each input line must contain `x`, `y`, `z` in `m/s^2`; an optional `observed_at` may be supplied. For a physical run, the file must be exported directly from the SBC before the live sensor is disconnected. Do not edit it after capture.

## Receipt and offline replay

```bash
python prototype/evidence_node_v01.py receipt \
  --observations run/observations.jsonl \
  --output run/receipt.json \
  --stimulus 3.0,7.0

# Copy run/ to another laptop, remove/disconnect the SBC and sensor, then:
python prototype/evidence_node_v01.py replay \
  --observations run/observations.jsonl \
  --receipt run/receipt.json
```

`replay` recomputes hashes, checks the chain and runs the objective vibration inspection. It prints exactly one terminal result: `PASS`, `FAIL`, or `UNRESOLVED`, plus reasons.

The capture adapter is intentionally not presented as complete hardware support. The physical wiring and acquisition driver remain an explicit missing step rather than being simulated by this repository.
