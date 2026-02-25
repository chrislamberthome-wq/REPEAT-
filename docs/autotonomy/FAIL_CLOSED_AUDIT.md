# REPEAT-Bounded Autotonomy — Fail-Closed Audit

This document audits every verifier pathway in the repository to confirm that
failures produce non-zero exit codes ("fail-closed") and that no pathway silently
warns and continues when a hard failure is required.

---

## 1. Simulation Exit Codes (`simulate_mram_runs.py`)

**File:** [`simulate_mram_runs.py`](../../simulate_mram_runs.py)

```python
# main() ~line 278
try:
    run_simulation(args.mode, args.seed, args.output)
    sys.exit(0)     # success
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)     # runtime error → fail-closed ✅
```

**Verdict:** ✅ Fail-closed on runtime errors.

**Note:** The simulation itself runs all N steps and records per-step verdicts in receipts.
It does NOT exit non-zero when individual runs fail drift detection — by design, it records
verdicts in JSONL for downstream audit. A consumer (e.g., `python -m verifier`) must check
receipts and exit non-zero if any verdict is `"pass": false`.

---

## 2. Gift-Log Verifier (`verify_giftlog.py`)

**File:** [`repeat_devops_gift_processing/verify_giftlog.py`](../../repeat_devops_gift_processing/verify_giftlog.py)

Module header documents exit codes:
```
Exit codes:
  0 = PASS
  1 = FAIL (issues found)
  2 = ERROR (runtime / file / schema error)
```

**Verdict:** ✅ Fail-closed. Non-zero exit on issues or errors. No silent warn-and-continue.

---

## 3. Canonical Verifier Entrypoint (`python -m verifier`)

**File:** [`verifier/__main__.py`](../../verifier/__main__.py)

Exit codes:
```
0 = all receipts valid
1 = validation failure (schema violation, hash mismatch, or failed verdict)
2 = runtime error (file not found, JSON parse error, etc.)
```

The verifier:
- Validates required fields against `schemas/repeat-spintronics-receipt-v1.schema.json`
- Validates `evidence_hash_sha256` and `receipt_hash_sha256` by recomputing hashes
- Exits non-zero on any failure (fail-closed) ✅
- Cross-receipt hash chain: **NOT validated** (chain is absent; absence is documented, not
  invented — see [`IMPLEMENTATION_MAP.md`](IMPLEMENTATION_MAP.md))

**Verdict:** ✅ Fail-closed.

---

## 4. CI Workflow Audit

### 4a. CI (`ci.yml`)

```yaml
- name: Run tests
  run: make test    # pytest exits non-zero on failure → fail-closed ✅
```

**Verdict:** ✅ pytest returns non-zero on test failure; `make test` propagates exit code.

### 4b. Diagnostics (`diag-check.yml`)

```yaml
- name: Run diagnostics (strict)
  run: make diag-strict    # exits non-zero on any diagnostic failure ✅
```

**Verdict:** ✅ Strict mode; fail-closed.

### 4c. Lint (`lint.yml`)

```yaml
- name: Lint with flake8
  run: |
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

**Note:** The second flake8 call uses `--exit-zero`, so style warnings do not block CI.
Only syntax errors and undefined names (E9, F63, F7, F82) are fail-closed. This is
intentional — style warnings are advisory, not blocking.

**Verdict:** ✅ Syntax/undefined-name errors are fail-closed; style warnings are advisory.

---

## 5. No "Warn and Continue" Gaps Found

After auditing all verifier pathways:

| Pathway | Fail-Closed? | Notes |
|---------|-------------|-------|
| `simulate_mram_runs.py` runtime errors | ✅ Yes | `sys.exit(1)` |
| `simulate_mram_runs.py` per-run verdicts | ⚠️ Records in JSONL | By design; downstream verifier must check |
| `verify_giftlog.py` FAIL | ✅ Yes | Exit code 1 |
| `verify_giftlog.py` ERROR | ✅ Yes | Exit code 2 |
| `python -m verifier` schema/hash failure | ✅ Yes | Exit code 1 |
| `python -m verifier` runtime error | ✅ Yes | Exit code 2 |
| CI: `make test` | ✅ Yes | pytest non-zero propagated |
| CI: `make diag-strict` | ✅ Yes | strict mode |
| CI: flake8 syntax errors | ✅ Yes | E9/F63/F7/F82 are hard failures |
| CI: flake8 style warnings | ⚠️ Advisory | `--exit-zero` intentional |

No "warn and continue" gaps were found in hard-failure pathways.

---

## 6. Absent Items (Documented, Not Invented)

- **Cross-receipt hash chain validation:** Not implemented; verifier does not check
  `prev_receipt_hash` (field does not exist in schema).
- **Schema validation via `jsonschema` library:** The `python -m verifier` performs
  structural field checks and hash recomputation. Full JSON Schema Draft-07 validation
  (using `jsonschema`) is optional and not required for fail-closed operation.
