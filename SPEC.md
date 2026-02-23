REPEAT / B4IU / IDA — Normative Spec v0.1 (One Page, PDF-ready)

# REPEAT / B4IU / IDA — Normative Spec v0.1

> **Scope:** Exploratory research tooling for CAG expansion simulation and probabilistic
> inference layers (HMM/HHMM). Not medical advice, not a biological truth engine.

---

## Bounded Autotonomy

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human
micro-approval only within predeclared constraints and only if each step produces an auditable
trace and a verifier can NACK/fail-closed (non-zero exit / invalid receipt).

This does **not** claim self-governing goal sovereignty, moral agency, or rights — only
autonomy of execution under mandatory verification.

For full definition, operational invariants, and implementation evidence, see:
[`docs/autotonomy/AUTOTONOMY.md`](docs/autotonomy/AUTOTONOMY.md)

---

## Operational Invariants (Normative)

1. Every run produces an append-only trace artifact (JSONL receipts).
2. A verifier deterministically classifies the run PASS/FAIL.
3. FAIL implies fail-closed: non-zero exit, CI failure, no "warn-only" path.
4. Receipts bind artifacts + provenance to tamper-evident hashes (sha256 / JCS C14N).

---

## Verification Entrypoints

| Entrypoint | Purpose |
|---|---|
| `python -m verifier <receipts.jsonl>` | Canonical receipt validator (fail-closed) |
| `python -m repeat_hd verify --infile <file>` | HD encoding integrity check |
| `python repeat_devops_gift_processing/verify_giftlog.py --input <csv>` | Gift log QA |
| `make test` | Full pytest suite |
| `make diag-strict` | Strict diagnostics (CI) |

---

## References

- [`docs/autotonomy/AUTOTONOMY.md`](docs/autotonomy/AUTOTONOMY.md) — normative definition
- [`docs/autotonomy/IMPLEMENTATION_MAP.md`](docs/autotonomy/IMPLEMENTATION_MAP.md) — evidence map
- [`docs/autotonomy/FAIL_CLOSED_AUDIT.md`](docs/autotonomy/FAIL_CLOSED_AUDIT.md) — fail-closed audit
- [`C14N_RULES.md`](C14N_RULES.md) — canonical JSON + hash rules
- [`governance/hallucination_policy.md`](governance/hallucination_policy.md) — claim governance
