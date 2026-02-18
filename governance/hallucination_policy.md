# Hallucination Governance Policy

## Purpose
Prevent **silent wrong** by ensuring the system does not present unverified claims as verified facts. Hallucination is treated as a **governance risk** (protocol breach), not a routine error.

## Definitions
- **Claim:** A statement that can be true/false in the real world (factual, numerical, procedural, attributional).
- **Evidence:** A verifier-linked artifact supporting a claim (tests, hashes, logs, receipts, citations).
- **Hallucination:** A claim presented as fact without adequate evidence when evidence is feasible, and later fails verification.

## Normative Requirements
### Claim typing
All nontrivial claims MUST be labeled as one of:
- `VERIFIED` — supported by evidence included or referenced.
- `INFERRED` — derived reasoning from verified inputs; inference is stated explicitly.
- `UNKNOWN` — not enough evidence; uncertainty is stated explicitly.

### Evidence requirements
- `VERIFIED` claims MUST include at least one evidence reference:
  - `file:` (path + hash), `test:` (test id), `receipt:` (receipt id/hash), or `cite:` (external citation).
- If verification is feasible but not performed, the claim MUST be `UNKNOWN`, not `VERIFIED`.

### Fail-closed behavior
When in doubt, the system MUST degrade to `UNKNOWN` and provide a verification path.

### No silent wrong
Outputs consumed by automation MUST treat claims without evidence references as **non-authoritative**.

## Measurement
- **Hallucination Rate (H):**
  - H = (# claims asserted as fact that fail verification) / (# claims asserted as fact)
- H MUST be computed over **claims**, not tokens.

## Enforcement Hooks
- CI MAY require:
  - a claim ledger for releases and high-impact docs
  - `claim-ledger lint` to ensure every `VERIFIED` claim has evidence refs

## Scope
Applies to:
- documentation intended to guide execution (runbooks, CI guidance, specs)
- outputs that influence decisions (benchmarks, comparisons, status reports)
- any “world-facing” statement where silent wrong is costly