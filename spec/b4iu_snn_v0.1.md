# B4IU-SNN v0.1 Specification

## Locks

- **Canonicalization:** follow `C14N_RULES.md`.
- **Hash:** SHA-256 over c14n bytes.
- **Trace hashchain:** `hash = sha256(c14n(event_without_hash))`.
- **FAIL-CLOSED.**

---

## A.1 Scope

B4IU-SNN v0.1 defines the minimal conformance gate for a single-node, single-network
REPEAT run that asserts bounded-locality (B4IU) behaviour in a spiking-neural-network
(SNN) context.

## A.2 Artifact set

A conforming run directory MUST contain exactly the following files:

| File | Role |
|------|------|
| `manifest.json` | lists all artifacts and `run_id` |
| `policy.json` | locality policy (`H_max`, allowed event types, hop exceptions) |
| `trace.jsonl` | append-only event log with hashchain |
| `receipt.json` | cryptographic summary (trace_root, ida_root, sha256_c14n) |
| `verdict.json` | final PASS/FAIL outcome |

## A.3 Trace hashchain

Each event carries:

```
hash = sha256(c14n(event_without_hash))
```

where `c14n` is JCS (RFC 8785) canonical JSON and `event_without_hash` is the
event object with the `hash` field removed before serialisation.

The first event's `prev_hash` MUST equal the genesis hash
`sha256:` + 64 zero hex digits.

## A.4 Receipt computation

```
receipt_body = {schema, run_id, trace_root, ida_root}
receipt.sha256_c14n = sha256(c14n(receipt_body))
```

`run_id` is taken from `manifest.json`. The verifier MUST recompute the receipt
and compare byte-for-byte (canonical form) against `receipt.json`.

## A.5 IDA root

Collect every event that carries a `unit_id`.  For each unique `unit_id`, record
`{"unit_id": uid}`.  If the same `unit_id` appears with inconsistent IDA fields
across events, FAIL.  Sort the collected unit entries by `unit_id` (ascending
Unicode codepoint) and hash:

```
ida_root = sha256(c14n([{unit_id: …}, …]))
```

## A.6 Locality policy

Events whose `event_type` is listed in `policy.locality_event_types` MUST carry
`hop_count`.

- If `hop_count > H_max` AND `unit_id` is NOT in `policy.hop_exceptions` → FAIL.
- If `hop_count <= H_max` AND `exception_reason` is not `null` → FAIL.

## A.7 Step structure

`STEP_START` and `STEP_END` events MUST be balanced (no unclosed steps at end of
trace).  The `step` field across all events MUST be non-decreasing.

## A.8 Verdict

`verdict.json` MUST be schema-valid and `verdict` MUST equal `"PASS"`.
