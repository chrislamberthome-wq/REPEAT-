# delta_repeat_proof_v1

> **Delta is no longer asserting governance; it is emitting governed execution receipts.**

## Artifact Description

A verifiable execution primitive that proves a governed decision occurred,
execution followed constraints, the result is reproducible, and verification
is independent.

## Structure

```
delta_repeat_proof_v1/
├── input/
│   └── cognitive_task.json      # One deterministic task (sum [1,2,3]=6)
├── schemas/
│   ├── event.schema.json        # Contract for each trace event
│   ├── governance.schema.json   # Contract for the governance decision record
│   └── receipt.schema.json      # Contract for the execution receipt
├── trace/
│   └── trace.jsonl              # Append-only, five-stage hash-chained trace
├── receipt/
│   └── receipt.json             # Execution receipt (status=PASS, trace_sha256)
├── verifier/
│   ├── canonical.py             # RFC 8785 canonical JSON + SHA-256
│   ├── replay.py                # Deterministic replay verifier
│   ├── receipt.py               # Receipt loader and verifier
│   └── verify.py                # Independent entry point (exit 0/1/2)
└── tests/
    ├── test_canonical.py
    ├── test_hash_chain.py
    ├── test_governance.py
    ├── test_replay.py
    └── test_receipt.py
```

## Five-Stage Cycle

Every execution follows exactly one fixed cycle:

| Seq | Stage    | Purpose                                      |
|-----|----------|----------------------------------------------|
| 1   | reflect  | Record the task and inputs                   |
| 2   | plan     | Record the execution strategy                |
| 3   | learn    | Record observations about the input domain   |
| 4   | regulate | Evaluate constraints before execution        |
| 5   | govern   | Emit the binary governance decision          |

## Governance Record

```json
{
  "decision_id": "gov-0001",
  "cycle_id": "cycle-0001",
  "verdict": "ALLOW",
  "constraints_applied": ["max_nodes<=3", "posture!=LOCKDOWN"]
}
```

`ALLOW` → execution proceeds and a `PASS` receipt is emitted.  
`DENY` → verifier halts immediately with `EXIT 1 FAIL`.

## Receipt Shape

```json
{
  "cycle_id": "cycle-0001",
  "issued_at": "2026-03-17T11:32:39Z",
  "status": "PASS",
  "trace_sha256": "sha256:<64 hex chars>"
}
```

## Verification Matrix Contract

| Condition            | Exit | Receipt |
|----------------------|------|---------|
| Baseline (valid run) | 0    | PASS    |
| Hash-chain failure   | 1    | FAIL    |
| Non-canonical JSON   | 1/2  | FAIL    |
| Replay mismatch      | 1    | FAIL    |
| Governance DENY      | 1    | FAIL    |

## Reproduction Steps

```bash
git clone https://github.com/chrislamberthome-wq/REPEAT-
cd REPEAT-/delta_repeat_proof_v1
python verifier/verify.py
```

Expected output:
```
PASS
```

## Running Unit Tests

```bash
cd delta_repeat_proof_v1
python -m pytest tests/ -v
```

## Running the Full Verification Matrix

```bash
python scripts/run_verification_matrix.py --json-output /tmp/matrix.json
```

## Acceptance Criteria (binary)

A valid run **must** produce:

1. A canonical trace (each line is RFC 8785 JSON).
2. An unbroken hash chain (every `prev_hash` matches the canonical hash of the
   previous event body).
3. An `ALLOW` governance verdict.
4. A successful deterministic replay (task output equals `expected_output`).
5. A receipt with `status = PASS` and a `trace_sha256` that matches the actual
   file.

Any violation of those conditions is **FAIL** (exit 1).  
Inability to determine validity due to malformed input or tooling fault is
**ERROR** (exit 2).
