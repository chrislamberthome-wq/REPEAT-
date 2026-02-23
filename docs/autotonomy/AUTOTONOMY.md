# Autotonomy (REPEAT-bounded)

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human micro-approval **only within predeclared constraints** and **only if each step produces an auditable trace and a verifier can NACK/fail-closed** (non-zero exit / invalid receipt).

This does **not** claim self-governing goal sovereignty, moral agency, or rights—only **autonomy of execution under mandatory verification**.

## Operational invariants

- Every run produces an append-only trace artifact (e.g., JSONL).
- A verifier deterministically classifies the run PASS/FAIL.
- FAIL implies fail-closed: non-zero exit, CI failure, no "warn-only" path.
- Receipts (if implemented) bind artifacts + provenance to tamper-evident hashes.

## Scope note

This repository is research tooling. "Autotonomy" here is bounded execution autonomy under verification, not product capability claims and not medical/clinical claims.
