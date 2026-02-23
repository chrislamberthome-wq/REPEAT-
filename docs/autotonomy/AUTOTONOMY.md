# Autotonomy — Normative Definition (REPEAT-bounded)

## Definition

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human
micro-approval only within predeclared constraints and only if each step produces an auditable
trace and a verifier can NACK/fail-closed (non-zero exit / invalid receipt).

This does **not** claim self-governing goal sovereignty, moral agency, or rights—only autonomy
of execution under mandatory verification.

---

## Scope

This definition applies exclusively to execution autonomy within this repository's research
tooling (CAG expansion simulation, MRAM drift detection, REPEAT-HD encoding). It carries no
implication of:

- self-governing goal sovereignty
- moral agency
- legal or ethical rights
- clinical or biological authority

---

## Operational Invariants

The following invariants are **normative** (MUST):

1. **Trace artifact** — Every run MUST produce an append-only trace artifact (e.g., JSONL receipt
   file). The artifact MUST be deterministic given the same inputs and seed.

2. **Verifier pass/fail** — A verifier MUST deterministically classify the run `PASS` or `FAIL`.
   The verifier verdict MUST be recorded in the trace artifact (`verdict.pass` field).

3. **Fail-closed** — `FAIL` implies fail-closed: non-zero exit code, CI failure, and no
   "warn-only" path. A verifier that returns zero on failure is a protocol breach.

4. **Receipts** — Receipts (where implemented) MUST bind artifacts and provenance to
   tamper-evident hashes (`packet_hash_sha256`, `evidence_hash_sha256`, `receipt_hash_sha256`).
   Hash computation follows `C14N_RULES.md` (JCS / RFC 8785).

---

## Relation to Repository Scope

This repository is an **exploratory research tool**. Autotonomy here means the simulation and
verification pipelines can run end-to-end without human approval of each step, provided:

- the run stays within the declared parameter space (schema-validated),
- every run produces a JSONL receipt,
- the verifier classifies the run and exits non-zero on failure.

Nothing in this definition extends to agentic deployment, autonomous decision-making outside
this bounded execution context, or any form of self-modification.

---

## References

- [IMPLEMENTATION_MAP.md](./IMPLEMENTATION_MAP.md) — evidence-backed map of where each
  invariant is currently implemented or absent
- [FAIL_CLOSED_AUDIT.md](./FAIL_CLOSED_AUDIT.md) — audit of all verify pathways
- [`C14N_RULES.md`](../../C14N_RULES.md) — canonical JSON + hash rules
- [`schemas/repeat-spintronics-receipt-v1.schema.json`](../../schemas/repeat-spintronics-receipt-v1.schema.json) — receipt schema
- [`governance/hallucination_policy.md`](../../governance/hallucination_policy.md) — claim governance policy
