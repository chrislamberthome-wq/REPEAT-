# Repository Boundary Audit — 2026-09-20

Repository inspected: [`chrislamberthome-wq/REPEAT-`](https://github.com/chrislamberthome-wq/REPEAT-/tree/main) at commit `24733965c658b740a70881434aebdab2a4a0c6bc`.

**No files were modified.**

The referenced PDF (`REPEAT_Finalized_Decisions_and_Immediate_Actions.pdf`) was not available as a repository file or accessible attachment in this inspection. Where the frozen PDF is required to establish semantic authority, the result is **FAIL-CLOSED**, not an inferred PASS.

## Summary

| Boundary | Finding |
|---|---|
| Product/commercial concepts must not control REPEAT semantics, schemas, receipts, verifier behavior, or governance | **FAIL-CLOSED** |
| Implementation must match the frozen `REPEAT_CORE_v1` | **FAIL-CLOSED** |
| Happy Ending proposal must not claim funding, validation, authority, or implementation status | **PASS** |
| Repository implementation/status claims must be evidence-backed | **FAIL** |
| Structural governance: locatable, precedence-declared `REPEAT_CORE_v1` authority | **FAIL** |
| Documentation accuracy: `README.md`, `DEPLOYMENT_BLOCKER.md` | **FAIL** |
| Policy enforcement: `governance/hallucination_policy.md` | **UNENFORCED** |
| Modification decision | **No modification authorized** |

## 1. Product/commercial authority over REPEAT semantics

**Finding: FAIL-CLOSED**

The Happy Ending document explicitly attempts to preserve the required separation:

- [`docs/external/THE_HAPPY_ENDING_FUNDING_PROPOSAL.md#L3-L5`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/docs/external/THE_HAPPY_ENDING_FUNDING_PROPOSAL.md#L3-L5) labels itself a "non-normative external proposal," outside normative implementation and governance paths.
- Lines 9–11: The Happy Ending may fund REPEAT but does not define it.
- Lines 17–23: explicitly disclaims changes to schemas, canonicalization, verifier behavior, governance, or protocol dependencies.
- Lines 27–29: no revenue relationship is currently verified.
- Lines 37–44: repeat the external/non-binding separation.

That is evidence of stated separation, not evidence that the separation is enforced mechanically.

The repository contains several independent or potentially competing receipt/schema surfaces:

- [`repeat-governance/schemas/receipt.schema.json`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/repeat-governance/schemas/receipt.schema.json)
- [`schemas/repeat-spintronics-receipt-v1.schema.json`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/schemas/repeat-spintronics-receipt-v1.schema.json)
- [`schema/repeat-spintronics-receipt-v1.schema.json`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/schema/repeat-spintronics-receipt-v1.schema.json)
- [`repeat_hd/hd/schemas/geno_receipt.v1.schema.json`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/repeat_hd/hd/schemas/geno_receipt.v1.schema.json)
- [`schemas/quasicrystal_receipt_v1.schema.json`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/schemas/quasicrystal_receipt_v1.schema.json)

The available evidence does not establish which of these, if any, is the frozen `REPEAT_CORE_v1` authority. The Happy Ending file is not shown to control any of them, but the repository also lacks an unambiguous machine-checkable declaration binding the normative core to one frozen schema/verifier set.

**Conclusion:** no proven commercial-authority violation, but the boundary cannot be certified from the available frozen oracle. **FAIL-CLOSED.**

## 2. Drift against `REPEAT_CORE_v1`

**Finding: FAIL-CLOSED**

A repository-wide search found no literal `REPEAT_CORE_v1` marker. The core boundary therefore cannot be mapped unambiguously to the current implementation.

- [`C14N_RULES.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/C14N_RULES.md) defines a C14N v1 algorithm and receipt hashing rules but does not identify itself as `REPEAT_CORE_v1`.
- [`SPEC.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/SPEC.md) identifies itself as "Normative Spec v0.1," not `REPEAT_CORE_v1`.
- [`tags/core-receipt-v1.0.0.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/tags/core-receipt-v1.0.0.md) refers to "core receipt functionality" but does not supply the frozen semantic boundary.
- [`node_zero_v1/verify.py`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/node_zero_v1/verify.py) contains only a stub:
  ```python
  def verify():
      pass
  ```
- The primary [`verifier/`](https://github.com/chrislamberthome-wq/REPEAT-/tree/main/verifier) implementation validates a different receipt shape (`run_id`, packet/evidence/receipt hashes, `verdict` object). Its relationship to the frozen core is not established by the repository.

Independent documentation/implementation drift:

- [`README.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/README.md) describes "SOLID-FSK v0.1," a geometric resonance communication experiment, and references `SPEC_SOLID_FSK_v0_1.md` and `golden/`, neither present in the repository tree.
- [`DEPLOYMENT_BLOCKER.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/DEPLOYMENT_BLOCKER.md#L4-L10) claims a working FastAPI server and HTTP surface; the referenced `server.main:app` and `docs/fixture.json` are not present in the inspected tree.

**Conclusion:** implementation drift is present at the documentation/status level; semantic drift against the PDF cannot be conclusively measured without the PDF's exact oracle. **FAIL-CLOSED**, with a concrete evidence-quality/status-drift issue.

## 3. Happy Ending proposal claims

**Finding: PASS**

- Explicitly marked non-normative.
- States funding "may" occur, not that it has.
- States no revenue relationship is verified.
- Disclaims authority over schemas, canonicalization, verifiers, receipts, governance, protocol behavior.
- Does not claim funding validates REPEAT or that implementation is funded/complete.

Path: [`docs/external/THE_HAPPY_ENDING_FUNDING_PROPOSAL.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/docs/external/THE_HAPPY_ENDING_FUNDING_PROPOSAL.md)

**PASS for the proposal's wording and placement**, subject to the caveat that repository-wide enforcement of that separation remains unproven (see Finding 5).

## 4. Evidence-backed validation and implementation status

**Finding: FAIL**

### Deployment blocker

[`DEPLOYMENT_BLOCKER.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/DEPLOYMENT_BLOCKER.md):

- Lines 4–10 claim a verified system, attributing failure solely to Replit deployment.
- Lines 13–42 claim a functioning FastAPI server, health endpoint, deterministic HTTP verifier, and `docs/fixture.json`.
- Lines 89–104 give commands using `server.main:app`.
- The inspected tree contains no `server/` directory and no `docs/fixture.json`.

The document's "VERIFIED SYSTEM / BLOCKED DEPLOY" status is not reproducible from the current tree. See Finding 6 on whether `governance/hallucination_policy.md` provides any mechanical backstop against this.

### README

[`README.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/README.md) describes a SOLID-FSK project while the repository contains multiple unrelated REPEAT, spintronics, governance, HD, and verifier artifacts. Its referenced specification and calibration directory are absent.

### Verifier evidence

[`verifier/__main__.py`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/verifier/__main__.py) contains actual receipt validation logic, but the repository does not establish that this verifier is the frozen `REPEAT_CORE_v1` verifier rather than one implementation track among several.

These are concrete status/provenance problems, not stylistic inconsistencies. **FAIL.**

## 5. Structural governance failure (added 2026-09-20)

**Finding: FAIL**

Five parallel receipt/schema files exist (listed in Finding 1) with no committed, machine-checkable declaration of precedence, and no locatable `REPEAT_CORE_v1` artifact anywhere in the tree. This holds independent of whether `THE_HAPPY_ENDING_FUNDING_PROPOSAL.md` ever attempts to influence any of them: even under a maximally charitable reading of Happy Ending's non-normative status, nothing in the repository can currently be certified as *the* core, because no single core is identified as such. This is a standalone governance gap, not a consequence of the commercial-boundary question in Finding 1.

## 6. Policy enforcement status: `governance/hallucination_policy.md` (added 2026-09-20)

**Finding: UNENFORCED**

[`governance/hallucination_policy.md`](https://github.com/chrislamberthome-wq/REPEAT-/blob/main/governance/hallucination_policy.md) defines claim typing (`VERIFIED`/`INFERRED`/`UNKNOWN`), evidence requirements, fail-closed defaults, and a "no silent wrong" principle. Its Enforcement Hooks section states:

> CI MAY require: a claim ledger for releases and high-impact docs / `claim-ledger lint` to ensure every `VERIFIED` claim has evidence refs

This is permissive ("MAY"), not mandatory language — the one clause capable of making the policy mechanically binding is optional by its own text. No claim-ledger file, lint script, or CI workflow referencing this policy was located in the repository. Full repository tree/code-search browsing was not accessible during this inspection (search and tree endpoints declined automated access), so absence cannot be certified with full crawl coverage — but no enforcement artifact was found anywhere it would be expected to appear (workflows, root lint config, README).

**Conclusion:** the policy is documentary/aspirational, not demonstrated to be enforced. Citations of this policy elsewhere in this audit (Finding 4) support the *should-be-flagged* conclusion but should not be read as evidence that flagging happens automatically.

## Modification decision

No modification should be made under the requested rule.

Concrete issues identified:

1. Unsupported or stale implementation/status claims (`README.md`, `DEPLOYMENT_BLOCKER.md`).
2. Unclear authority among multiple schema and verifier tracks, with no locatable `REPEAT_CORE_v1`.
3. No committed enforcement mechanism for the claims-evidence policy that would otherwise catch (1).

Correcting these would require semantic decisions — which specification, schema, receipt format, verifier, and status claims are authoritative — that are not frozen in the material available to this inspection.

> **Do not modify the repository. Record the audit as FAIL-CLOSED pending the authoritative `REPEAT_Finalized_Decisions_and_Immediate_Actions.pdf` or an equivalent committed boundary artifact, and pending a committed, mandatory (not "MAY") enforcement mechanism for `governance/hallucination_policy.md`.**

Repository-wide code search may be incomplete: [GitHub code search for `REPEAT_CORE_v1`](https://github.com/chrislamberthome-wq/REPEAT-/search?q=REPEAT_CORE_v1&type=code).