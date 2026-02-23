# Implementation Map — REPEAT Autotonomy

This document maps the normative autotonomy invariants to concrete implementation evidence in this repository.

## Invariant 1: Every run produces an append-only trace artifact (JSONL)

**Evidence:**

- `simulate_mram_runs.py` writes JSONL receipts to an output file (default `mram_receipts.jsonl`):

  ```python
  # simulate_mram_runs.py:234-236
  with open(output_file, 'w') as f:
      for receipt in receipts:
          f.write(json.dumps(receipt, sort_keys=True) + '\n')
  ```

- Each receipt includes canonical JSON settings (keys sorted, no whitespace — JCS/RFC 8785 compatible via `simulate_mram_runs.py:31-37`) and hash fields: `packet_hash_sha256`, `evidence_hash_sha256`, `receipt_hash_sha256`.

- Schema: `schemas/repeat-spintronics-receipt-v1.schema.json` — enforces `^sha256:[a-f0-9]{64}$` on all hash fields and requires `verdict`, `metrics`, `run_id`, `measured_resistance_ohms`.

## Invariant 2: A verifier deterministically classifies the run PASS/FAIL

**Evidence:**

- `verifier/mram_receipts.py` implements deterministic hash recomputation (evidence hash and receipt hash) and schema checks (required fields, sha256: prefix, fail_reason presence).
- `verifier/__main__.py` provides `python -m verifier <file>` with exit codes:
  - `0` — PASS (all receipts pass integrity checks)
  - `2` — FAIL (schema or hash check failed)
  - `1` — Error (missing file, parse error, unexpected exception)

## Invariant 3: FAIL implies fail-closed (non-zero exit, CI failure)

**Evidence:**

- `verifier/__main__.py` exits with code 2 on FAIL, code 1 on error — both non-zero.
- `Makefile` `verify` target runs `python -m verifier mram_receipts.jsonl`; non-zero exit propagates as make failure.
- `Makefile` `ci` target runs `simulate`, `verify`, `test`, `ci-count-b4iu` in sequence; any failure stops the chain.
- `.github/workflows/ci.yml` step `Run CI (fail-closed)` runs `make ci`; CI job fails on non-zero exit.

## Invariant 4: Receipts bind artifacts + provenance to tamper-evident hashes

**Evidence (partial):**

- `simulate_mram_runs.py:40-44` computes `sha256:<hex>` of canonical JSON:

  ```python
  def sha256_c14n(obj: Dict[str, Any]) -> str:
      canonical_bytes = canonical_json(obj)
      digest = hashlib.sha256(canonical_bytes).hexdigest()
      return f"sha256:{digest}"
  ```

- `evidence_hash_sha256` binds the receipt data (excluding hash fields) to a tamper-evident digest.
- `receipt_hash_sha256` binds the full receipt including `evidence_hash_sha256`.

**Absent / not yet implemented:**

- **Hash chain** (each receipt chaining the previous receipt hash): not present in current schema or simulation.
- **Provenance block** (committer, timestamp, environment): not present in receipts.

## Workflows

- `.github/workflows/ci.yml`: runs `make ci` (simulate → verify → test → ci-count-b4iu).
- `.github/workflows/lint.yml`: runs flake8 linting on Python source.
- `.github/workflows/diag-check.yml`: diagnostic checks (`make diag-strict`).
- `.github/workflows/pages.yml`: GitHub Pages deployment.
