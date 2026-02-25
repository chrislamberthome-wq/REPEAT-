# REPEAT-Bounded Autotonomy

## Normative Definition

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human
micro-approval only within predeclared constraints and only if each step produces an auditable
trace and a verifier can NACK/fail-closed (non-zero exit / invalid receipt).

This does not claim self-governing goal sovereignty, moral agency, or rights—only autonomy of
execution under mandatory verification.

---

## Scope

This definition applies to research tooling in this repository. It is explicitly
**not a product claim**, not a claim of general-purpose AI autonomy, and not a claim of
self-direction beyond the predeclared execution envelope.

---

## Operational Invariants

The following invariants MUST hold for any execution that claims REPEAT-bounded autotonomy:

- **INV-1 (Predeclared constraints):** The execution envelope (input schema, verifier parameters,
  drift tolerances, allowed actions) MUST be declared before execution begins, not inferred
  post-hoc.

- **INV-2 (Auditable trace):** Every executed step MUST emit a structured trace record (JSONL
  receipt or equivalent) containing: run identifier, input hash, measured output, verdict
  (pass/fail), and evidence hash.

- **INV-3 (Fail-closed verifier):** A verifier MUST exist that can NACK any step. NACK MUST
  produce a non-zero exit code. "Warn and continue" without exit-code failure is not permitted
  when the invariant is claimed.

- **INV-4 (No goal sovereignty):** The system does not select or modify its own constraints,
  evaluation criteria, or reward signals without explicit human authorization. It does not claim
  moral agency or rights.

- **INV-5 (Replay / deterministic re-run):** Given the same input packet and seed, the execution
  MUST produce byte-identical receipts. This enables independent audit.

- **INV-6 (Hash chain / provenance, if present):** If cross-receipt linking is implemented,
  each receipt MUST reference the hash of the preceding receipt, forming a tamper-evident chain.
  If absent, absence MUST be documented (see
  [`IMPLEMENTATION_MAP.md`](IMPLEMENTATION_MAP.md)).

---

## Relationship to REPEAT Protocol

REPEAT (Reproducible Execution Protocol with Evidence and Auditable Traces) enforces INV-1
through INV-5 at the protocol level:

- The **packet** encodes predeclared constraints (INV-1).
- The **receipt JSONL** encodes the auditable trace (INV-2).
- The **verifier** enforces fail-closed exit on schema violation or verdict failure (INV-3).
- Deterministic simulation with fixed seed provides replay (INV-5).

Cross-receipt hash chain (INV-6) is **not currently implemented**. See
[`IMPLEMENTATION_MAP.md`](IMPLEMENTATION_MAP.md) for details.

---

## What This Is Not

- **Not self-governing goal sovereignty:** The system cannot modify its own objectives,
  expand its own authority, or override human-set constraints.
- **Not moral agency:** No claims of ethical reasoning, rights, or autonomous value formation.
- **Not a product claim:** This is exploratory research tooling. No warranties of fitness
  for any purpose.
- **Not biological truth:** The simulation models MRAM physics for research; it does not
  certify device behavior or biological mechanisms.
