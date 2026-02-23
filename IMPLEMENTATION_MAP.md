# IMPLEMENTATION MAP — REPEAT-bounded Autotonomy

## Definition

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without
human micro-approval only within predeclared constraints and only if each step produces an
auditable trace and a verifier can NACK/fail-closed (non-zero exit / invalid receipt).

This does **not** claim self-governing goal sovereignty, moral agency, or rights — only
autonomy of execution under mandatory verification.

---

## Operational Invariants

| # | Invariant | Status |
|---|-----------|--------|
| 1 | Every run produces an append-only trace artifact (JSONL). | ✅ Implemented — `simulate_mram_runs.py` writes `--output <file>.jsonl` |
| 2 | A verifier deterministically classifies the run PASS/FAIL. | ✅ Implemented — `repeat_hd/cli.py::cmd_verify` and `simulate_mram_runs.py::verify_run` |
| 3 | FAIL implies fail-closed: non-zero exit, CI failure, no warn-only path. | ✅ Implemented — `cmd_verify` returns exit code 1 (decode/CRC fail) or 2 (invariant violation); `simulate_mram_runs.py` exits 0 only on clean execution |
| 4 | Receipts bind artifacts + provenance to tamper-evident hashes. | ⚠️  Partially implemented — `simulate_mram_runs.py` computes `sha256_c14n` evidence + receipt hashes per REPEAT C14N v1; the `repeat_hd` CLI verifier does **not** yet produce receipt artifacts |

---

## Code Locations

### Trace artifact production

| File | Purpose |
|------|---------|
| `simulate_mram_runs.py` | Simulation engine; writes one JSONL receipt per run to `--output <path>` (default `mram_receipts.jsonl`) |
| `C14N_RULES.md` | Normative canonicalization spec (JCS / RFC 8785) used to compute tamper-evident hashes |

### Verifier (PASS/FAIL, fail-closed)

| File | Symbol | Behavior |
|------|--------|----------|
| `repeat_hd/cli.py` | `decode_data()` | Returns `(str, bool, list[str])`; `is_valid=False` on CRC mismatch or parse error |
| `repeat_hd/cli.py` | `check_invariants()` | Returns list of invariant violations (null bytes, length mismatch, re-encoding mismatch) |
| `repeat_hd/cli.py` | `cmd_verify()` | Returns **1** on decode/CRC failure, **2** on `--strict` invariant violation, **0** on PASS |
| `repeat_hd/cli.py` | `main()` | Propagates `cmd_verify` return code to `sys.exit()` |
| `simulate_mram_runs.py` | `verify_run()` | Returns `(pass_status, fail_reason)`; checks threshold and drift tolerance |
| `simulate_mram_runs.py` | `main()` | `sys.exit(0)` on success, `sys.exit(1)` on unhandled exception |

### Receipts / provenance hashing

| File | Symbol | Notes |
|------|--------|-------|
| `simulate_mram_runs.py` | `sha256_c14n()` | Computes `sha256:` hex of canonical JSON |
| `simulate_mram_runs.py` | `create_receipt()` | Builds per-run receipt with `evidence_hash_sha256` and `receipt_hash_sha256` |
| `C14N_RULES.md` | — | Normative algorithm; receipt exclusion procedure documented |

### CI / test infrastructure

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | Runs `make ci-count-b4iu` (locked B4IU counter), then `make test` (pytest) |
| `.github/workflows/diag-check.yml` | Runs `make diag-strict` (claim-ledger lint in strict mode) |
| `.github/workflows/lint.yml` | Runs `flake8` syntax checks |
| `Makefile` | `test`, `ci-count-b4iu`, `diag-strict` targets |
| `tests/` | pytest suite — `test_cli.py`, `test_codec_3d.py`, `test_mram_drift_detection.py` |

---

## Reproducing a Run Locally

### Encode and verify (repeat_hd CLI)

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Encode data
python -m repeat_hd encode "hello world" > /tmp/encoded.bin

# Verify (fail-closed: exits non-zero on any failure)
python -m repeat_hd verify --infile /tmp/encoded.bin
# With strict invariant checks:
python -m repeat_hd verify --strict --infile /tmp/encoded.bin

# Run full test suite
make test
```

### MRAM drift-detection simulation

```bash
# Stable run — produces JSONL trace
python3 simulate_mram_runs.py --mode pass --seed 42 --output /tmp/mram_pass.jsonl

# Drift-failure run — same trace format, contains FAIL receipts
python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output /tmp/mram_drift.jsonl
```

Trace artifacts are written to the path given by `--output` (JSONL, one receipt per line).
Each line contains `verdict.pass`, `evidence_hash_sha256`, and `receipt_hash_sha256`.

### Diagnostics (strict claim-ledger lint)

```bash
make diag-strict
```

---

## Missing / Unimplemented Features

The following features are **not** currently present in this repository.
They are listed here for transparency; they must not be assumed to exist.

| Feature | Status | Notes |
|---------|--------|-------|
| `repeat_hd verify` receipt output | ❌ Not implemented | The CLI verifier does not write a JSONL receipt; it only prints PASS/FAIL to stderr |
| Replay / deterministic re-execution | ❌ Not implemented | No mechanism to replay a prior run from stored receipts |
| Tamper-evident receipt chain | ⚠️  Partial | `simulate_mram_runs.py` hashes individual receipts; no chain/Merkle structure |
| Automated receipt validation in CI | ❌ Not implemented | CI runs tests and linting but does not validate previously stored receipts |
| Agent goal-setting / plan selection | ❌ Not applicable | This is research tooling; no autonomous goal-setting or planning system exists |

---

## Scope Reminder

This repository is **research tooling** for simulating somatic CAG expansion dynamics and
overlaying probabilistic inference layers. It is not a biological truth engine, not a clinical
decision support system, and not a self-governing agent. All autonomy is execution-scoped and
bounded by the verifier constraints described above.

See `README.md` and `governance/hallucination_policy.md` for further scope guardrails.
