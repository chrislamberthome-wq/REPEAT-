# Fail-Closed Audit — REPEAT Autotonomy

This document audits the fail-closed guarantees of the REPEAT autotonomy implementation.

## Current state (pre-PR)

### Issue 1: `simulate_mram_runs.py` exits 0 even with failed verdicts

`simulate_mram_runs.py` always calls `sys.exit(0)` on successful completion (line 280), regardless of how many verdicts have `pass: false`. A simulation run with 100% drift failures still exits 0.

**Status:** Known limitation. The simulation script is a data producer, not a verifier. The verifier (`verifier/mram_receipts.py`) handles integrity checks. Per explicit policy decision, the verifier does **not** fail on `verdict.pass == false` — only on schema/hash integrity violations. A separate policy check would be required to gate on verdict outcomes.

### Issue 2: CI called missing Makefile targets (pre-PR)

Before this PR, the CI workflow called `make ci-count-b4iu` and `make test`, but the Makefile only defined `all`, `clean`, and `install`. Both CI steps would fail with `make: *** No rule to make target`.

**Status:** Fixed in this PR — all required targets are now defined.

### Issue 3: `ci-count-b4iu` was not fail-closed on missing file (pre-PR)

A one-liner that blindly opens `mram_receipts.jsonl` without checking existence would raise a Python exception rather than a clean non-zero exit, producing unclear CI errors.

**Status:** Fixed in this PR — the `ci-count-b4iu` target explicitly calls `sys.exit(1)` when the file is missing or contains zero non-empty lines.

## Changes in this PR

| Component | Change | Fail-closed guarantee |
|-----------|--------|-----------------------|
| `Makefile` | Added `simulate`, `test`, `verify`, `ci-count-b4iu`, `ci` targets | `ci` fails if any step exits non-zero |
| `verifier/__init__.py` | New file | Package marker |
| `verifier/__main__.py` | New file | exits 2 on FAIL, 1 on error, 0 on PASS |
| `verifier/mram_receipts.py` | New file | NACK on hash mismatch, missing required fields, missing `fail_reason` |
| `.github/workflows/ci.yml` | Replaced `make test` with `make ci`; removed redundant standalone `make ci-count-b4iu` step | CI fails on any verifier or test failure |
| `README.md` | Appended Autotonomy section | Documents bounded autonomy policy |
| `SPEC.md` | Expanded to full normative spec | Documents operational invariants |
| `docs/autotonomy/AUTOTONOMY.md` | New file | Normative definition + scope note |
| `docs/autotonomy/IMPLEMENTATION_MAP.md` | New file | Evidence-backed invariant mapping |

## Policy decision: `verdict.pass==false` does not fail verification

By explicit policy, the verifier does **not** fail when `verdict.pass == false`. The verifier checks **integrity** only: schema compliance, hash recomputation, required field presence, and `fail_reason` presence when `pass` is false. Whether a failing verdict is acceptable in a given context is a higher-level policy concern outside this verifier's scope.

## Remaining gaps

- Hash chain not implemented (receipts do not chain each other's hashes).
- Provenance block not implemented (no committer/timestamp/environment binding in receipts).
- `simulate_mram_runs.py` always exits 0; a separate policy check to gate on verdict outcomes would need to be added explicitly if required.
