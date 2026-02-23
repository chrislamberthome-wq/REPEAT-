# REPEAT-bounded Autotonomy — Implementation Map

Evidence-backed map of where each autotonomy invariant is (or is not) implemented
in commit `389e3ddf470c643e84cd925eaffa9054e70adff1`.

---

## 1. Trace emission (JSONL or equivalent)

**Status: PRESENT**

- **`simulate_mram_runs.py`** — emits one receipt per run as a JSONL line:

  ```python
  # lines 234-236
  with open(output_file, 'w') as f:
      for receipt in receipts:
          f.write(json.dumps(receipt, sort_keys=True) + '\n')
  ```

  Invoked as:
  ```
  python3 simulate_mram_runs.py --mode pass --seed 42 --output receipts.jsonl
  ```

- **`ai_loopback_visual_binary/tools/trace_run.py`** — a separate trace helper;
  exists but is not yet wired into a CI pipeline.

---

## 2. Verifier pass/fail (exit-code fail-closed)

**Status: PARTIALLY PRESENT — `simulate_mram_runs.py` exits non-zero on exception;
canonical standalone verifier added at `verifier/__main__.py` (see Commit 3).**

- **`simulate_mram_runs.py`** — exits non-zero on unhandled exception:

  ```python
  # lines 278-283
  try:
      run_simulation(args.mode, args.seed, args.output)
      sys.exit(0)
  except Exception as e:
      print(f"Error: {e}", file=sys.stderr)
      sys.exit(1)
  ```

- **`simulate_mram_runs.py` `verify_run()`** — per-run PASS/FAIL logic:

  ```python
  # lines 124-145
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

- **`verifier/thermal_resonance.py`** — stub class; no exit-code enforcement
  present in this file (only a skeleton `compute()` method).

- **`verifier/__main__.py`** — **ADDED** in this PR; validates JSONL receipts
  against the schema and recomputed hashes; exits non-zero on any failure.

---

## 3. Receipt / hash chain / provenance

**Status: PRESENT (single-receipt hashes); chain across receipts: ABSENT**

- **`simulate_mram_runs.py` `create_receipt()`** — computes two tamper-evident hashes:

  ```python
  # lines 148-180
  # evidence_hash: sha256_c14n of receipt without receipt_hash_sha256
  evidence_hash = sha256_c14n(receipt_data)
  receipt_data["evidence_hash_sha256"] = evidence_hash

  # receipt_hash: sha256_c14n of full receipt (including evidence_hash)
  receipt_hash = sha256_c14n(receipt_data)
  receipt_data["receipt_hash_sha256"] = receipt_hash
  ```

- **`simulate_mram_runs.py` `sha256_c14n()` / `canonical_json()`** — C14N v1
  implementation (JCS / RFC 8785):

  ```python
  # lines 21-44
  def canonical_json(obj):
      return json.dumps(obj, ensure_ascii=False, sort_keys=True,
                        separators=(',', ':'), allow_nan=False).encode('utf-8')

  def sha256_c14n(obj):
      canonical_bytes = canonical_json(obj)
      digest = hashlib.sha256(canonical_bytes).hexdigest()
      return f"sha256:{digest}"
  ```

- **`schemas/repeat-spintronics-receipt-v1.schema.json`** — receipt schema
  requiring `packet_hash_sha256`, `evidence_hash_sha256`, `receipt_hash_sha256`.

- **Cross-receipt hash chain (e.g., each receipt commits to the previous
  `receipt_hash_sha256`):** **NOT PRESENT**. Each receipt is independently
  hashed; there is no Merkle-style chaining between receipts in the JSONL.

---

## 4. Replay / deterministic re-run

**Status: PRESENT**

- **`simulate_mram_runs.py`** — `--seed` flag seeds `random.Random` for full
  determinism:

  ```python
  # lines 183-186
  def run_simulation(mode, seed, output_file):
      rng = random.Random(seed)
      ...
  ```

  Same seed + mode produces identical JSONL output and identical hashes
  (verified by `tests/test_mram_drift_detection.py::test_receipt_hashes_deterministic`).

- **`tests/test_mram_drift_detection.py`** — golden-vector tests lock in
  deterministic behavior:

  ```python
  EXPECTED_PACKET_HASH = "sha256:e79de2a174f42f074d36fc450a8389fe16d804996535d2a462f4c815ba4b3353"
  EXPECTED_RUN_23_RECEIPT_HASH = "sha256:24957fd9ea82a4197f8afac0fe11c0002453b2f6942129f1d683c08fa452c127"
  ```

---

## Summary table

| Invariant | Present? | Primary file(s) |
|---|---|---|
| Trace emission (JSONL) | ✅ Yes | `simulate_mram_runs.py` |
| Verifier fail-closed (exit code) | ✅ Yes (simulator + new `verifier/__main__.py`) | `simulate_mram_runs.py`, `verifier/__main__.py` |
| Receipt / tamper-evident hashes | ✅ Yes (per-receipt) | `simulate_mram_runs.py`, `schemas/` |
| Cross-receipt hash chain | ❌ Absent | — |
| Replay / deterministic re-run | ✅ Yes | `simulate_mram_runs.py --seed` |
| Schema validation in CI | ✅ Yes (via `verifier/__main__.py` + `make test`) | `verifier/__main__.py`, `Makefile` |
