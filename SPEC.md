REPEAT / B4IU / IDA — Normative Spec v0.1 (One Page, PDF-ready)

## Autotonomy (REPEAT-bounded)

**Definition:** The system may select plans and execute steps without human micro-approval
only within predeclared constraints and only if each step produces an auditable trace and a
verifier can NACK/fail-closed (non-zero exit / invalid receipt).

This does **not** claim self-governing goal sovereignty, moral agency, or rights — only
autonomy of execution under mandatory verification. The scope is bounded research tooling;
language in this spec is deliberately non-claimy and avoids product or marketing framing.

### Operational invariants

1. Every run produces an append-only trace artifact (e.g., JSONL).
2. A verifier deterministically classifies the run PASS/FAIL.
3. FAIL implies fail-closed: non-zero exit, CI failure, no warn-only path.
4. Receipts (if implemented) bind artifacts and provenance to tamper-evident hashes per
   REPEAT C14N v1 (see `C14N_RULES.md`).

See [IMPLEMENTATION_MAP.md](IMPLEMENTATION_MAP.md) for the mapping of these invariants to
concrete code locations, CLI entrypoints, and an explicit list of missing/unimplemented
features.