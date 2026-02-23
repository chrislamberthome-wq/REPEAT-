# Fail-Closed Enforcement Audit

> **Purpose:** Audit all verification pathways in this repository to ensure non-zero exit on
> failure and no "warn and continue" in CI paths.

---

## Audit Scope

The following verifier entry points were audited:

1. `simulate_mram_runs.py` — MRAM drift detection simulation + receipts
2. `repeat_hd/cli.py` — REPEAT-HD encode/verify CLI
3. `repeat_devops_gift_processing/verify_giftlog.py` — gift log QA verifier
4. `verifier/thermal_resonance.py` — thermal resonance module (stub)
5. `verifier/__main__.py` — canonical verifier entrypoint (added this PR)
6. CI workflows: `.github/workflows/ci.yml`, `lint.yml`, `diag-check.yml`

---

## 1. `simulate_mram_runs.py`

### Before this PR (gap)

`run_simulation()` did not return `fail_count`. `main()` called `sys.exit(0)` unconditionally
after a successful `run_simulation()` call, even if individual runs inside the simulation
reported `FAIL` verdicts and wrote `"pass": false` to the JSONL receipt.

```python
# BEFORE (gap): exits 0 even when fail_count > 0
try:
    run_simulation(args.mode, args.seed, args.output)
    sys.exit(0)
except Exception as e:
    sys.exit(1)
```

This means a CI job running `simulate_mram_runs.py --mode drift_fail` would exit 0 despite
drift failures being recorded in the receipts — a "warn and continue" equivalent.

### After this PR (fixed)

`run_simulation()` now returns `fail_count`. `main()` exits with `sys.exit(1)` if
`fail_count > 0`:

```python
# AFTER (fixed): exits 1 if any run fails
fail_count = run_simulation(args.mode, args.seed, args.output)
sys.exit(1 if fail_count > 0 else 0)
```

**Result: PASS — fail-closed enforced.**

---

## 2. `repeat_hd/cli.py`

**Status: PASS — already fail-closed before this PR.**

```python
# CRC/parse failure
print("VERIFICATION FAILED", file=sys.stderr)
return 1

# Strict invariant violations
print("STRICT MODE VIOLATIONS DETECTED", file=sys.stderr)
return 2
```

`sys.exit(main())` at entry point propagates non-zero returns as exit codes. No "warn-only"
path found.

---

## 3. `repeat_devops_gift_processing/verify_giftlog.py`

**Status: PASS — already fail-closed before this PR.**

Documented exit codes:
```
0 = PASS
1 = FAIL (issues found)
2 = ERROR (runtime / file / schema error)
```

No "warn and continue" path found; `--strict` flag can extend FAIL to medium/low issues.

---

## 4. `verifier/thermal_resonance.py`

**Status: STUB — no verification logic.**

```python
class ThermalResonance:
    def compute(self):
        pass   # no verification, no exit code
```

This file is a class stub only. It has no verification logic, no exit code, and no CI
integration. It is not wired into any CI pathway. **No fix needed for CI fail-closed
purposes**, but this absence is documented.

---

## 5. `verifier/__main__.py` (added this PR)

**Status: PASS — canonical entrypoint, fail-closed.**

Provides `python -m verifier` as the canonical verification entrypoint. Validates:
- Schema compliance of JSONL receipt files
- Required fields per `schemas/repeat-spintronics-receipt-v1.schema.json`
- Hash integrity (`receipt_hash_sha256` recomputed and compared)

Exits non-zero on any validation failure.

---

## 6. CI Workflows

### `.github/workflows/ci.yml`

- Runs `make test` — pytest suite; fails on test failures (non-zero exit propagated)
- Runs `make ci-count-b4iu` — B4IU term counter; exits non-zero if count changes unexpectedly
- **Status: PASS** after Makefile targets added in this PR.

### `.github/workflows/lint.yml`

- Runs `flake8 . --count --select=E9,F63,F7,F82` — hard-fails on syntax errors / undefined names
- Runs `flake8 . --count --exit-zero ...` — soft check (warnings only); this is intentional
  and acceptable (not a CI-critical path)
- **Status: PASS** — critical lint path is fail-closed.

### `.github/workflows/diag-check.yml`

- Runs `make diag-strict` — strict diagnostics; target added to Makefile in this PR
- Previously: `make diag-strict` was missing from Makefile → CI would fail with `make: *** No rule to make target 'diag-strict'`
- **Status: FIXED** — Makefile target added.

---

## Summary

| Component | Was Fail-Closed? | After This PR |
|---|---|---|
| `simulate_mram_runs.py` | ❌ Gap: exited 0 on run failures | ✅ Fixed: exits 1 if `fail_count > 0` |
| `repeat_hd/cli.py` | ✅ Yes | ✅ No change needed |
| `verify_giftlog.py` | ✅ Yes | ✅ No change needed |
| `verifier/thermal_resonance.py` | N/A (stub) | N/A (stub, not CI-wired) |
| `verifier/__main__.py` | N/A (absent) | ✅ Added, fail-closed |
| CI `make test` | ❌ Target missing | ✅ Added to Makefile |
| CI `make ci-count-b4iu` | ❌ Target missing | ✅ Added to Makefile |
| CI `make diag-strict` | ❌ Target missing | ✅ Added to Makefile |
| `requirements.txt` | ❌ Missing (used by `diag-check.yml`) | ✅ Added |

---

## Gaps Not Fixed (Out of Scope)

- **Hash chain (`prev_hash`):** No sequential chaining of receipts. Per-run receipts are
  independently tamper-evident but not chain-linked. This would require schema changes and is
  not a fail-closed gap (receipts still exit non-zero on failure).
- `verifier/thermal_resonance.py`: remains a stub. Adding verification logic would require
  understanding the thermal resonance model, which is out of scope.
