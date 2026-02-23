# Autotonomy Implementation Map

> **Evidence-backed.** All claims below are supported by file paths and excerpts found via
> code search. Absence is explicitly documented.

---

## Evidence Gathering

The following searches were used to gather evidence (equivalent to `rg` commands specified in
the issue):

**Search 1** — trace/receipt/hash patterns:
```
pattern: receipt|hash.chain|chain_hash|prev_hash|state_hash|trace\.jsonl|jsonl
```

**Search 2** — verifier/fail-closed patterns:
```
pattern: verif|verify|assert|FAIL|fail.closed|sys\.exit|returncode
```

**Search 3** — REPEAT/IDA/B4IU in docs:
```
pattern: Platoputer|IDA|B4IU|REPEAT  (in docs/)
```

**Search 4** — CI/Makefile/workflow references:
```
pattern: Makefile|ci|github/workflows
```

---

## 1. Trace Emission (JSONL or equivalent)

**Status: PRESENT** — `simulate_mram_runs.py` produces append-only JSONL receipt files.

- **[`simulate_mram_runs.py:233–236`](../../simulate_mram_runs.py)** — writes receipts to JSONL:
  ```python
  for receipt in receipts:
      f.write(json.dumps(receipt, sort_keys=True) + '\n')
  ```
- **[`simulate_mram_runs.py:9–10`](../../simulate_mram_runs.py)** — CLI output paths documented:
  ```
  python3 simulate_mram_runs.py --mode pass --seed 42 --output receipts.jsonl
  ```
- **[`docs/probes/GYRO-IPHN-0001_SPEC.md:90`](../probes/GYRO-IPHN-0001_SPEC.md)** — probe spec requires audit trace:
  ```
  audit trace: audit.jsonl with pass/fail checks + hashes
  ```
- **[`tests/test_mram_drift_detection.py:30`](../../tests/test_mram_drift_detection.py)** — tests verify JSONL output is produced:
  ```python
  with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
  ```
- **[`.gitignore:29`](../../.gitignore)** — `*.jsonl` excluded from version control (expected runtime artifact).

**Hash chain (prev_hash linking runs): ABSENT** — receipts contain per-run hashes
(`packet_hash_sha256`, `evidence_hash_sha256`, `receipt_hash_sha256`) but no chained
`prev_hash` linking consecutive receipts. Each receipt is independently verifiable but not
chain-linked. No `chain_hash` or `prev_hash` fields found.

---

## 2. Verifier Pass/Fail (Exit Code Fail-Closed)

**Status: PRESENT in simulation + HD CLI; STUB in `verifier/`**

- **[`simulate_mram_runs.py:280–283`](../../simulate_mram_runs.py)** — exits non-zero on failure (fixed in this PR):
  ```python
  fail_count = run_simulation(args.mode, args.seed, args.output)
  sys.exit(1 if fail_count > 0 else 0)
  ```
  > **Before this PR (gap):** `main()` called `sys.exit(0)` unconditionally after
  > `run_simulation()` regardless of `fail_count`. Fixed: `run_simulation()` now returns
  > `fail_count` and `main()` exits 1 if `fail_count > 0`. See `FAIL_CLOSED_AUDIT.md`.

- **[`repeat_hd/cli.py:139,155,159`](../../repeat_hd/cli.py)** — HD verify command exits non-zero:
  ```python
  print("VERIFICATION FAILED", file=sys.stderr)
  ...
  return 1   # CRC/parse failure
  return 2   # strict invariant violation
  ```

- **[`repeat_devops_gift_processing/verify_giftlog.py:10–11`](../../repeat_devops_gift_processing/verify_giftlog.py)** — gift log verifier:
  ```
  Exit codes:  0 = PASS,  1 = FAIL (issues found),  2 = ERROR
  ```

- **[`verifier/thermal_resonance.py`](../../verifier/thermal_resonance.py)** — **STUB only**:
  ```python
  class ThermalResonance:
      def compute(self):
          pass   # no verification logic, no exit code
  ```
  This file contains no verification logic and no fail-closed behavior.

- **Canonical `python -m verifier` entrypoint: PRESENT** (added as part of this PR) —
  see [`verifier/__main__.py`](../../verifier/__main__.py).

---

## 3. Receipt / Hash Chain / Provenance

**Status: PRESENT (per-run receipts); hash chain ABSENT**

- **[`schemas/repeat-spintronics-receipt-v1.schema.json`](../../schemas/repeat-spintronics-receipt-v1.schema.json)** — receipt schema requires:
  ```json
  "required": ["schema", "packet_hash_sha256", "evidence_hash_sha256",
               "receipt_hash_sha256", "run_id", ...]
  ```

- **[`simulate_mram_runs.py:148–180`](../../simulate_mram_runs.py)** — `create_receipt()` builds tamper-evident receipts:
  ```python
  evidence_hash = sha256_c14n(receipt_data)
  receipt_data["evidence_hash_sha256"] = evidence_hash
  receipt_hash = sha256_c14n(receipt_data)
  receipt_data["receipt_hash_sha256"] = receipt_hash
  ```

- **[`C14N_RULES.md`](../../C14N_RULES.md)** — canonical JSON hash rules (JCS / RFC 8785):
  ```
  Hash format: "sha256:" + 64 lowercase hex.
  Receipt exclusion: compute sha256 over the object with `receipt` removed.
  ```

- **[`repeat_hd/hd/schemas/geno_receipt.v1.schema.json`](../../repeat_hd/hd/schemas/geno_receipt.v1.schema.json)** — geno receipt schema with `raw_data_hashes.sha256[]` field.

- **[`ai_loopback_visual_binary/audit/receipts/run-000001.receipt.json`](../../ai_loopback_visual_binary/audit/receipts/run-000001.receipt.json)** — minimal receipt artifact:
  ```json
  { "schema": "v1.0", "receipt": { "receipt_id": "AI_LOOPBACK-000001", ... } }
  ```

**Hash chain (prev_hash / chain_hash): ABSENT** — no field linking receipt N to receipt N-1.
Tamper-evidence is per-receipt only; a sequence of receipts cannot be chain-verified.

---

## 4. Replay / Deterministic Re-run

**Status: PRESENT**

- **[`simulate_mram_runs.py`](../../simulate_mram_runs.py)** — `--seed` argument enables deterministic replay:
  ```python
  parser.add_argument("--seed", type=int, default=42, ...)
  ```

- **[`tests/test_mram_drift_detection.py:118–137`](../../tests/test_mram_drift_detection.py)** — `test_receipt_hashes_deterministic` proves bit-for-bit reproducibility:
  ```python
  for i, (r1, r2) in enumerate(zip(receipts1, receipts2)):
      assert r1 == r2, f"Receipt {i+1} differs between runs"
      assert r1['receipt_hash_sha256'] == r2['receipt_hash_sha256']
  ```

- **[`tests/test_mram_drift_detection.py:24`](../../tests/test_mram_drift_detection.py)** — golden hash pinned for regression:
  ```python
  EXPECTED_RUN_23_RECEIPT_HASH = "sha256:24957fd9ea82a4197f8afac0fe11c0002453b2f6942129f1d683c08fa452c127"
  ```

---

## 5. CI / Makefile / Workflow Coverage

- **[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)** — runs `make test` and `make ci-count-b4iu`
- **[`.github/workflows/lint.yml`](../../.github/workflows/lint.yml)** — runs `flake8`
- **[`.github/workflows/diag-check.yml`](../../.github/workflows/diag-check.yml)** — runs `make diag-strict`
- **[`Makefile`](../../Makefile)** — `test`, `ci-count-b4iu`, and `diag-strict` targets added in this PR

---

## Summary Table

| Invariant | Status | Primary Evidence |
|---|---|---|
| Trace emission (JSONL) | ✅ Present | `simulate_mram_runs.py:233–236` |
| Verifier PASS/FAIL | ✅ Present (partial) | `simulate_mram_runs.py:280–283`, `repeat_hd/cli.py:139` |
| Fail-closed exit codes | ⚠️ Partial gap | See `FAIL_CLOSED_AUDIT.md` |
| Receipt / hash provenance | ✅ Present | `schemas/repeat-spintronics-receipt-v1.schema.json` |
| Hash chain (prev_hash) | ❌ Absent | No `chain_hash`/`prev_hash` found anywhere |
| Deterministic replay | ✅ Present | `simulate_mram_runs.py --seed`, golden hash tests |
| Canonical verifier entrypoint | ✅ Added | `verifier/__main__.py` (this PR) |
