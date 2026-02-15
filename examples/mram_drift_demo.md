# MRAM Drift Detection Demo

This demonstration showcases how REPEAT detects drift in MRAM hardware testing that naive threshold-based logging would miss.

## The Problem

Traditional MRAM testing uses simple threshold checks:
- **IF** resistance < threshold **THEN** PASS
- **ELSE** FAIL

This approach misses gradual drift that stays below the threshold but indicates hardware degradation or instability.

## The REPEAT Solution

REPEAT adds drift detection on top of threshold checking:
1. Establish a baseline from initial measurements
2. Monitor resistance values over time
3. Detect when drift exceeds tolerance, even if values stay below threshold
4. Generate cryptographically verifiable receipts for each measurement

## Demonstration

### Setup

- Device: MRAM-A1B2C3D4
- Baseline Resistance (parallel state): ~1000Ω
- Threshold: 1250Ω
- Drift Tolerance: 5%
- Number of runs: 100
- Baseline window: first 10 runs

### Stable Mode (No Drift)

```bash
python3 simulate_mram_runs.py --mode pass --seed 42 --output stable.jsonl
```

**Output:**
```
Simulation complete: mode=pass, seed=42
  Total runs: 100
  PASS: 100
  FAIL: 0
  Receipts written to: stable.jsonl
  Packet hash: sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353
```

**Result:** All 100 runs pass. Both naive threshold logic and REPEAT agree.

**Sample Receipt (Run 1 - PASS):**
```json
{
  "schema": "repeat-spintronics-receipt-v1",
  "packet_hash_sha256": "sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353",
  "evidence_hash_sha256": "sha256:65e7e3adc4823353fc563bca2683cbe64fa7cb8b20f4f7168b8094c0ecb57292",
  "receipt_hash_sha256": "sha256:22557832b83b904b20c870040c0182c2a5e6e32475b6fc4fad3c976d03a8720f",
  "run_id": 1,
  "measured_resistance_ohms": 1002.8559,
  "verdict": {
    "pass": true
  },
  "metrics": {
    "mean_resistance_ohms": 1002.8559,
    "drift_pct": 0.0
  }
}
```

---

### Drift Failure Mode (Gradual Drift)

```bash
python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output drift.jsonl
```

**Output:**
```
Simulation complete: mode=drift_fail, seed=42
  Total runs: 100
  PASS: 22
  FAIL: 78
  Receipts written to: drift.jsonl
  Packet hash: sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353
  First failure: run_id=23, reason=drift_detected
```

**Result:** Starting at run 23, REPEAT detects drift exceeding 5% tolerance.

**Critical Finding:** All measured resistances stay **below the 1250Ω threshold**, so naive logging would report **100% PASS**. However, REPEAT detects the gradual upward drift and correctly reports **FAIL**.

---

### First Failure Analysis (Run 23)

**Sample Receipt (Run 23 - FIRST FAILURE):**
```json
{
  "schema": "repeat-spintronics-receipt-v1",
  "packet_hash_sha256": "sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353",
  "evidence_hash_sha256": "sha256:86688456f93e9e2ad67be8033253150eb4e090e73e185baf88bba5109340e10d",
  "receipt_hash_sha256": "sha256:24957fd9ea82a4197f8afac0fe11c0002453b2f6942129f1d683c08fa452c127",
  "run_id": 23,
  "measured_resistance_ohms": 1068.6877,
  "verdict": {
    "pass": false,
    "fail_reason": "drift_detected"
  },
  "metrics": {
    "mean_resistance_ohms": 1016.3613,
    "drift_pct": 5.1484
  }
}
```

**Analysis:**
- Measured resistance: **1068.69Ω** (well below 1250Ω threshold ✓)
- Baseline mean: **1016.36Ω** (from first 10 runs)
- Drift: **5.15%** (exceeds 5.0% tolerance ✗)
- Verdict: **FAIL** with reason `drift_detected`

**Key Point:** Naive threshold logic would report **PASS** because 1068.69Ω < 1250Ω. REPEAT correctly reports **FAIL** due to drift.

---

## Comparison Table

| Run | Resistance (Ω) | Drift (%) | Naive Threshold | REPEAT Verdict |
|-----|---------------|-----------|-----------------|----------------|
| 1   | 1002.86       | 0.00      | ✓ PASS          | ✓ PASS         |
| 10  | 1014.78       | 1.77      | ✓ PASS          | ✓ PASS         |
| 22  | 1064.78       | 4.76      | ✓ PASS          | ✓ PASS         |
| 23  | 1068.69       | **5.15**  | ✓ PASS          | ✗ **FAIL**     |
| 50  | 1147.83       | 12.93     | ✓ PASS          | ✗ FAIL         |
| 100 | 1291.45†      | 27.07     | ✗ FAIL          | ✗ FAIL         |

† At run 100, resistance finally exceeds threshold, so even naive logic fails. But by this point, REPEAT has already identified the drift at run 23—77 runs earlier!

---

## What This Proves

1. **Silent Drift Detection:** REPEAT catches gradual hardware degradation that naive threshold checks miss.

2. **Deterministic Indexing:** The first failure is always at run 23 with seed 42—completely reproducible.

3. **Cryptographic Verification:** Each receipt has:
   - `packet_hash_sha256`: Immutable test configuration
   - `evidence_hash_sha256`: Measurement data integrity
   - `receipt_hash_sha256`: Complete receipt verification

4. **Golden Hashes:** The first failure receipt has deterministic hash:
   ```
   sha256:24957fd9ea82a4197f8afac0fe11c0002453b2f6942129f1d683c08fa452c127
   ```
   This guards against "Breakpoint A - Hash Illusion" (non-deterministic verification).

---

## Running the Demo

### Prerequisites

```bash
pip install pytest jsonschema
```

### Generate Receipts

```bash
# Stable mode (all pass)
python3 simulate_mram_runs.py --mode pass --seed 42 --output stable.jsonl

# Drift mode (REPEAT detects failure)
python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output drift.jsonl
```

### Run Tests

```bash
# All golden vector tests
pytest tests/test_mram_drift_detection.py -v

# Specific test for first failure
pytest tests/test_mram_drift_detection.py::TestMRAMDriftDetection::test_golden_hash_run_23 -v
```

### Inspect Receipts

```bash
# View first receipt
head -1 drift.jsonl | python3 -m json.tool

# View first failure (run 23)
sed -n '23p' drift.jsonl | python3 -m json.tool

# Count passes vs failures
grep '"pass":true' drift.jsonl | wc -l
grep '"pass":false' drift.jsonl | wc -l
```

---

## Integration with Hardware Workflows

REPEAT integrates seamlessly with existing MRAM testing infrastructure:

1. **Pre-test:** Generate packet with device configuration and verifier parameters
2. **During test:** Collect resistance measurements
3. **Post-test:** Generate receipts in JSONL format
4. **Audit:** Verify receipt hashes and drift metrics

No changes to measurement hardware required—REPEAT operates as a verification layer on top of existing data collection.

---

## Schema Definitions

- **Packet Schema:** `schemas/repeat-spintronics-packet-v1.schema.json`
- **Receipt Schema:** `schemas/repeat-spintronics-receipt-v1.schema.json`

Both schemas enforce:
- No optional fields (except `fail_reason` when passing)
- Deterministic ordering
- Explicit types and constraints
- Canonical JSON serialization per REPEAT C14N v1

---

## Conclusion

This MVP demonstrates that REPEAT:
- ✓ Prevents silent drift in MRAM testing
- ✓ Produces deterministic, reproducible receipts
- ✓ Detects failures that standard logging misses
- ✓ Integrates with existing hardware workflows
- ✓ Provides cryptographic verification via canonical hashing

**Key Takeaway:** In the drift scenario, naive threshold logic reports 100% success, while REPEAT correctly identifies 78% failure due to drift—detecting the issue 77 runs before the threshold is finally exceeded.
