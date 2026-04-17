# delta_repeat_proof_v1

> Delta is no longer asserting governance; it is emitting governed execution receipts.

## Overview

`delta_repeat_proof_v1` is a minimal, fully executable proof artifact that
demonstrates governed execution with an externally verifiable audit trail.

Every claimed property is machine-checkable:

| Guarantee | Check |
|---|---|
| Canonical trace | Each JSONL line is in JCS / RFC 8785 form |
| Unbroken hash chain | `event_hash` and `prev_hash` chain across all 5 events |
| ALLOW governance verdict | `trace/governance.json` → `verdict == "ALLOW"` |
| Deterministic replay | `sum([1,2,3]) == 6` re-executed from `input/cognitive_task.json` |
| Receipt integrity | `trace_sha256` and `crc16_ccitt_false` re-derived from raw bytes |

## Acceptance criteria

A run either:

- **PASS** — all five guarantees satisfied, receipt emitted with `status = PASS`.
- **FAIL** — explicit violation: DENY verdict, replay mismatch, broken hash chain,
  non-canonical JSON, or schema violation.
- **ERROR** — structural fault: missing file, invalid JSON, tooling failure.

FAIL and ERROR are both fail-closed. The verifier never continues past a detected
violation.

## Structure

```
delta_repeat_proof_v1/
├── input/
│   └── cognitive_task.json      # one deterministic task: sum([1,2,3])=6
├── schemas/
│   ├── event.schema.json        # strict schema for trace events
│   ├── governance.schema.json   # strict schema for governance records
│   └── receipt.schema.json      # strict schema for receipts
├── trace/
│   ├── trace.jsonl              # five-stage cycle (reflect→plan→learn→regulate→govern)
│   └── governance.json          # binary governance record (ALLOW)
├── receipt/
│   └── receipt.json             # governed execution receipt (status=PASS)
├── verifier/
│   ├── canonical.py             # JCS canonical JSON + SHA-256 + CRC-16
│   ├── replay.py                # deterministic task re-execution
│   ├── receipt.py               # receipt construction and verification
│   └── verify.py                # orchestrates all six checks
└── tests/
    ├── test_canonical.py
    ├── test_hash_chain.py
    ├── test_governance.py
    ├── test_replay.py
    └── test_receipt.py
```

## Running the verifier

```bash
pip install jsonschema
python -m delta_repeat_proof_v1.verifier.verify
```

Expected output:
```json
{
  "status": "PASS",
  "message": "all guarantees satisfied"
}
```

## Running the tests

```bash
pip install pytest jsonschema
pytest delta_repeat_proof_v1/tests/ -v
```

## Five-stage cycle

The trace records one complete cognitive cycle:

1. **reflect** — observe the task
2. **plan** — choose the operation
3. **learn** — record the result
4. **regulate** — verify output bounds
5. **govern** — emit governance decision

## Fixed conditions

- One deterministic task: `sum([1, 2, 3]) == 6`
- One five-stage cycle: `reflect → plan → learn → regulate → govern`
- One governance decision: `ALLOW`
- One append-only trace: 5 events with hash chain
- One receipt: `status = PASS`
- No optional fields. No best-effort recovery. No warnings that still pass.
