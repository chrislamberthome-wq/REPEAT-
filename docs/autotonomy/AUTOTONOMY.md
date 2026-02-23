# Autotonomy (REPEAT-bounded)

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human micro-approval **only within predeclared constraints** and **only if each step produces an auditable trace and a verifier can NACK/fail-closed** (non-zero exit / invalid receipt).  
This does **not** claim self-governing goal sovereignty, moral agency, or rights—only autonomy of execution under mandatory verification.

## Operational invariants (normative)

- Every run produces an append-only trace artifact (e.g., JSONL).
- A verifier deterministically classifies the run PASS/FAIL.
- FAIL implies fail-closed: non-zero exit, CI failure, no "warn-only" path.
- Receipts (if implemented) bind artifacts + provenance to tamper-evident hashes.

## Scope note

This document defines autonomy of **execution** only—the right to run a predeclared plan and produce a verifiable trace. It does not define:

- Goal sovereignty (the system cannot set its own goals)
- Moral agency (the system is not a moral agent)
- Rights or legal personhood
- Self-modification of constraints

Any expansion of autotonomy boundaries requires explicit human authorization and a corresponding update to this document.
