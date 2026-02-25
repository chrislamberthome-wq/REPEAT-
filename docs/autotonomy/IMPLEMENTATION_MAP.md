# REPEAT-Bounded Autotonomy — Implementation Map

This document maps each component of REPEAT-bounded autotonomy (as defined in
[`AUTOTONOMY.md`](AUTOTONOMY.md)) to concrete code paths in this repository.
Items that are **absent** are explicitly marked as such rather than inferred or invented.

---

## 1. Trace Emission (JSONL / Auditable Receipt)

**Status: PRESENT**

Every simulation run emits a JSONL receipt file. Each line is a structured JSON receipt.

**Primary implementation:** [`simulate_mram_runs.py`](../../simulate_mram_runs.py)

Key function:
```python
# simulate_mram_runs.py, function create_receipt() ~line 148
def create_receipt(packet, packet_hash, run_id, measured_resistance,
                   baseline_mean, drift_pct, verdict_pass, fail_reason):
    receipt_data = {
        "schema": "repeat-spintronics-receipt-v1",
        "packet_hash_sha256": packet_hash,
        "run_id": run_id,
        "measured_resistance_ohms": round(measured_resistance, 4),
        "verdict": {"pass": verdict_pass},
        "metrics": {"mean_resistance_ohms": ..., "drift_pct": ...}
    }
    # evidence_hash_sha256 and receipt_hash_sha256 appended before write
```

Receipts are written as JSONL (one JSON object per line):
```python
# simulate_mram_runs.py, function run_simulation() ~line 234
with open(output_file, 'w') as f:
    for receipt in receipts:
        f.write(json.dumps(receipt, sort_keys=True) + '\n')
```

**Schema:** [`schemas/repeat-spintronics-receipt-v1.schema.json`](../../schemas/repeat-spintronics-receipt-v1.schema.json)

Required fields per schema: `schema`, `packet_hash_sha256`, `evidence_hash_sha256`,
`receipt_hash_sha256`, `run_id`, `measured_resistance_ohms`, `verdict`, `metrics`.

**Tests:** [`tests/test_mram_drift_detection.py`](../../tests/test_mram_drift_detection.py)
- `test_receipt_schema_compliance` — validates required fields are present
- `test_receipt_hashes_deterministic` — validates byte-stability of hashes across runs
- `test_golden_hash_run_23` — golden-hash regression for run 23 (first drift failure)

---

## 2. Verifier Pass/Fail (Exit-Code Fail-Closed)

**Status: PRESENT (simulation-level); canonical entrypoint added (see below)**

### 2a. Simulation-level verifier

[`simulate_mram_runs.py`](../../simulate_mram_runs.py), function `verify_run()` (~line 124):
```python
def verify_run(run_id, measured_resistance, baseline_mean, packet):
    threshold = packet["verifier"]["threshold_resistance_ohms"]
    drift_tolerance = packet["verifier"]["drift_tolerance_percent"]
    if measured_resistance > threshold:
        return False, "threshold_exceeded"
    if run_id > packet["verifier"]["baseline_window_size"]:
        drift_pct = compute_drift_percentage(measured_resistance, baseline_mean)
        if abs(drift_pct) > drift_tolerance:
            return False, "drift_detected"
    return True, ""
```

The simulation itself exits 0 on success, 1 on runtime error (via `sys.exit(1)` in `main()`).
Individual run verdicts are recorded in receipts (`"verdict": {"pass": false}`), not as
process exit codes — the simulation runs all N steps and records verdicts.

### 2b. Canonical verifier entrypoint (`python -m verifier`)

**Status: ADDED** — [`verifier/__main__.py`](../../verifier/__main__.py)

This validates receipt schema and required fields, checks hashes, and exits fail-closed
(non-zero) on any validation failure. See [`FAIL_CLOSED_AUDIT.md`](FAIL_CLOSED_AUDIT.md).

### 2c. Gift-log verifier

[`repeat_devops_gift_processing/verify_giftlog.py`](../../repeat_devops_gift_processing/verify_giftlog.py)

Exit codes documented in module header:
```
Exit codes:
  0 = PASS
  1 = FAIL (issues found)
  2 = ERROR (runtime / file / schema error)
```

---

## 3. Receipt / Hash / Provenance

**Status: PRESENT (per-receipt self-hash); cross-receipt hash chain ABSENT**

### 3a. Per-receipt evidence hash and receipt hash (PRESENT)

Each receipt contains two hashes computed via canonical JSON (JCS / RFC 8785):

```python
# simulate_mram_runs.py ~line 172
evidence_hash = sha256_c14n(receipt_data)          # hash before receipt_hash field
receipt_data["evidence_hash_sha256"] = evidence_hash
receipt_hash = sha256_c14n(receipt_data)            # hash of full receipt
receipt_data["receipt_hash_sha256"] = receipt_hash
```

The `sha256_c14n` function ([`simulate_mram_runs.py`](../../simulate_mram_runs.py) ~line 40)
implements REPEAT C14N v1 (JCS / RFC 8785): UTF-8, keys sorted lexicographically,
no insignificant whitespace, `"sha256:" + 64 hex chars`.

Canonicalization rules: [`C14N_RULES.md`](../../C14N_RULES.md)

### 3b. Packet hash (PRESENT)

The packet is hashed before simulation and embedded in every receipt:
```python
packet_hash = sha256_c14n(packet)
# ...
receipt_data = {"packet_hash_sha256": packet_hash, ...}
```

This links every receipt to the predeclared constraint set (INV-1).

### 3c. Cross-receipt hash chain (ABSENT — not implemented)

**ABSENT.** There is no `prev_receipt_hash` or equivalent field linking receipt N to receipt
N-1. Each receipt is self-contained but not chained. If cross-receipt tamper-evidence is
required, this must be implemented explicitly.

---

## 4. Replay / Deterministic Re-run

**Status: PRESENT**

The simulation uses a seeded PRNG for all measurements:
```python
# simulate_mram_runs.py ~line 186
rng = random.Random(seed)
```

Given identical `--mode`, `--seed`, and packet configuration, the simulation produces
byte-identical JSONL receipts. This is validated by:

[`tests/test_mram_drift_detection.py`](../../tests/test_mram_drift_detection.py):
- `test_receipt_hashes_deterministic` — runs with seed 123 twice, asserts all receipts equal
- `test_golden_hash_run_23` — pins golden hash `sha256:24957fd9...` for run 23 with seed 42
- `test_packet_hash_invariant` — pins golden packet hash `sha256:e79de2a1...` across modes

Usage:
```bash
python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output receipts.jsonl
```

---

## Summary Table

| INV | Component | Status | Code Path |
|-----|-----------|--------|-----------|
| INV-1 | Predeclared constraints (packet schema) | ✅ Present | `simulate_mram_runs.py:create_packet()`, `schemas/repeat-spintronics-packet-v1.schema.json` |
| INV-2 | Auditable trace (JSONL receipts) | ✅ Present | `simulate_mram_runs.py:create_receipt()`, `run_simulation()` |
| INV-3 | Fail-closed verifier (non-zero exit) | ✅ Present | `verifier/__main__.py`, `verify_giftlog.py` |
| INV-4 | No goal sovereignty | ✅ By design | No self-modification of constraints; documented in `AUTOTONOMY.md` |
| INV-5 | Replay / deterministic re-run | ✅ Present | `simulate_mram_runs.py` seeded RNG; `tests/test_mram_drift_detection.py` |
| INV-6 | Cross-receipt hash chain | ❌ Absent | Not implemented; absence documented here |
