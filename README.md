# README

## Scope

This repository is an **exploratory research tool** for simulating somatic CAG expansion dynamics and overlaying probabilistic inference layers (HMM/HHMM) to study model behavior and interpretability.

It explicitly:
- **Does not provide medical advice** or clinical decision support.
- **Is not a biological truth engine** and does not certify disease mechanisms.
- **Is not a substitute for validation** against empirical datasets.
- **Prioritizes reproducibility, transparency, and safe interpretation**.

See [SCOPE.md](SCOPE.md) for full details, including non-goals, interpretation boundaries, and guardrails for new features.

## Execution Autonomy (REPEAT-bounded autotonomy)

The tooling in this repository operates under **REPEAT-bounded autotonomy**:

> The system may select plans and execute steps without human micro-approval only within
> predeclared constraints and only if each step produces an auditable trace and a verifier
> can NACK/fail-closed (non-zero exit / invalid receipt).

This does **not** imply self-governing goal sovereignty, moral agency, rights, or independence.
Scope is limited to execution autonomy under mandatory verification — this remains research
tooling, not a product or autonomous agent system.

Operational invariants:
- Every run produces an append-only trace artifact (JSONL).
- A verifier deterministically classifies the run PASS/FAIL.
- FAIL implies fail-closed: non-zero exit, CI failure, no warn-only path.
- Receipts (where implemented) bind artifacts and provenance to tamper-evident hashes.

See [IMPLEMENTATION_MAP.md](IMPLEMENTATION_MAP.md) for the full definition, code locations,
and an explicit list of missing/unimplemented features.
