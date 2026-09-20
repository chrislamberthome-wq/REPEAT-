# REPEAT Boundary Authority v1

## Status

This document is a governance boundary record. It does not certify the semantics of `REPEAT_CORE_v1`.

The core authority is currently:
- **Authority:** `REPEAT_CORE_v1`
- **Registration Status:** `pending`
- **Semantic Certification:** `uncertified`

Until semantic certification is separately established, core evaluation is **FAIL-CLOSED**.

## Mechanical Registration vs. Semantic Certification

`s schemas/CORE_INDEX.v1.json` is a mechanical registration and precedence artifact. It records:
- Artifact identifiers
- Repository-relative paths
- Artifact types and classifications (`candidate`, `normative`, `non-normative`)
- Verified SHA-256 digests or staging placeholders
- The declared seven-tier precedence order

Mechanical registration proves only that an artifact is uniquely named and placed within the governance index. It does **not** prove that the artifact's contents implement the frozen REPEAT core, that its semantics are fully verified, or that it is approved as normative.

Semantic certification requires an independent, explicit certification decision against the applicable frozen specification. Registered candidate artifacts remain candidates until certified.

## 7-Tier Precedence Hierarchy

In the event of a structural or semantic conflict across repository surfaces, the following explicit precedence ordering governs (from highest to lowest authority):

1. **`REPEAT_CORE_v1` Source Authority** (Root Governance & Frozen Commit)
2. **`schemas/CORE_INDEX.v1.json`** (Machine-Readable Registry Index)
3. **`docs/boundary-authority-v1.md`** (Human-Readable Governance Boundary)
4. **`schemas/REPEAT_v1.json`** (Canonical Core Schema Specification)
5. **`C14N_RULES.md`** (Canonicalization & Hashing Specification)
6. **`verifier/` Engine** (Executable Verifier Implementation)
7. **`audits/2026-09-20_repeat-core-boundary-audit.md`** (Historical Audit Record)

## Isolation Rules

All artifacts outside the explicit core registry—including multi-schema extensions under `repeat-governance/`, `repeat_hd/`, exploratory research documents under `docs/external/`, and commercial or deployment proposals—are classified as **non-normative extensions**.

Non-normative artifacts must not define or override core schemas, canonicalization rules, receipt semantics, verifier behavior, terminal outcomes, or governance precedence.

## Pending-State Policy

While `REPEAT_CORE_v1.status` is `pending` or `semantic_certification` is `uncertified`:
- No artifact may be presented as the semantically certified core.
- Precedence resolution may identify a registered winner, but must not imply semantic approval.
- Unresolved, missing, malformed, duplicate, or conflicting registrations are **FAIL-CLOSED**.
- Verifier execution must not infer authority from unregistered implementations.
- Absence of proof of authority is treated as absence of authority.
