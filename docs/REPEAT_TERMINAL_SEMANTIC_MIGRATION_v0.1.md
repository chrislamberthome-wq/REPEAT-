# REPEAT Terminal Semantic Migration v0.1

## 1. Purpose and status

This document defines a migration boundary for terminal semantic outcomes in REPEAT-. It is a design and review artifact, not implementation authorization. The existing verifier, schemas, Makefile, and `SCIENTIFIC_OVERVIEW.md` remain unchanged by this document.

The migration boundary explicitly supersedes the binary-only semantic assumption once this model is frozen and implementation is separately authorized. Until then, existing behavior must not be interpreted as already implementing the four-terminal model described here.

## 2. Four terminal semantics

The future terminal semantic model has exactly four named outcomes:

- **PASS** — The declared proposition is supported by admissible evidence under the declared rules, with all mandatory preconditions satisfied.
- **FAIL** — The declared proposition is evaluated against admissible evidence and is not supported under the declared rules, with all mandatory preconditions satisfied.
- **UNRESOLVED** — The evidence and rules are valid and admissible, but they do not deterministically justify either PASS or FAIL.
- **FAIL_CLOSED** — Evaluation is prohibited because an integrity, schema, parse, provenance, or mandatory-precondition requirement failed.

These terminals are semantic outcomes, not aliases for process success or failure.

## 3. Decision precedence

Integrity, schema, parse, provenance, and mandatory-precondition failures must prevent semantic evaluation. Therefore, **FAIL_CLOSED precedes proposition evaluation**. A verifier must not produce PASS, FAIL, or UNRESOLVED from evidence that cannot first be established as admissible under the applicable requirements.

After all required preconditions pass, the proposition may evaluate to PASS, FAIL, or UNRESOLVED. UNRESOLVED must not collapse into FAIL, whether because of caller preference, a convenience default, an exit-code convention, or an incomplete migration.

A conceptual precedence order is:

1. Establish integrity, schema validity, parse validity, provenance, and mandatory preconditions.
2. If any such requirement fails, return FAIL_CLOSED and do not evaluate the proposition.
3. Otherwise evaluate the proposition and return PASS, FAIL, or UNRESOLVED.

## 4. Legacy mapping

The legacy system exposes or may expose binary or error-shaped results. The following are migration considerations, not an authorization to reinterpret existing outputs in place:

- Existing `verdict.pass=true` is a candidate mapping to PASS only when the receipt, evidence, rules, provenance, and all mandatory preconditions are independently valid.
- Existing `verdict.pass=false` is a candidate mapping to FAIL only when the proposition was actually evaluated over admissible evidence and the result is a proposition failure rather than an infrastructure or precondition failure.
- Existing `ERROR` is not mechanically equivalent to any single future terminal. It may require migration logic to distinguish FAIL_CLOSED from an evaluation result of FAIL or UNRESOLVED.
- Existing schema, hash, runtime, parse, integrity, or provenance failures are candidates for FAIL_CLOSED, but the mapping requires migration logic that establishes the precise failure class and prevents accidental proposition evaluation.

No legacy value may be mechanically promoted where its origin, preconditions, or evaluation path are ambiguous. In particular, a legacy `false` must not be treated as FAIL when it may encode an error, missing evidence, invalid receipt, or unresolved evaluation. A legacy `ERROR` must not be treated as FAIL_CLOSED without confirming that the error represents a boundary failure rather than an evaluated proposition outcome.

## 5. Schema authority

No existing receipt schema is silently promoted to authoritative terminal semantics by this document. Existing schemas remain existing schemas until a separately reviewed migration changes their authority.

The future authoritative semantic field is reserved conceptually as an explicit terminal field whose value is one of `PASS`, `FAIL`, `UNRESOLVED`, or `FAIL_CLOSED`. Its exact field name, containing schema, validation rules, versioning, compatibility behavior, and production use are not defined as implemented here. Those details require a later schema decision and migration authorization.

Until that decision is frozen and implemented, no current field should be represented as though it were already the authoritative four-terminal semantic field.

## 6. Exit codes

Process exit status is separate from the semantic terminal. Unix exit codes such as 0, 1, or 2 must not become the protocol semantics and must not be used as the authoritative representation of PASS, FAIL, UNRESOLVED, or FAIL_CLOSED.

A future implementation may define a process-status policy for automation, diagnostics, or transport failure, but that policy must preserve the semantic terminal independently and unambiguously. Consumers must not infer the terminal solely from a process exit code.

## 7. UNRESOLVED

Valid and admissible evidence can legitimately produce UNRESOLVED. This occurs when the declared evidence and rules are usable and all mandatory preconditions pass, but the available information does not deterministically justify either proposition outcome.

UNRESOLVED is deterministic and auditable: the same declared evidence, rules, versions, and evaluation context must yield the same terminal, together with enough recordable basis to explain why neither PASS nor FAIL was justified.

UNRESOLVED cannot be converted to PASS or FAIL by caller preference, a default branch, an automation convention, or a desire for a binary answer. Any policy that requires a binary action must handle UNRESOLVED as a distinct input rather than rewriting its semantic meaning.

## 8. Independent verification

Verifier B must independently consume the declared evidence and declared rules. It must independently apply the integrity, schema, parse, provenance, mandatory-precondition, and proposition-evaluation requirements needed to derive the terminal.

Agreement on the same terminal between Verifier A and Verifier B is reproducibility evidence. It is not sufficient for Verifier B to import, call, delegate to, or otherwise reuse Verifier A's decision function.

Verifier B must independently detect altered evidence, including changes that would affect integrity, provenance, admissibility, or the proposition result. A shared result is meaningful only when the evidence and decision path are independently checked.

## 9. Migration gates

The four-terminal semantic model may be frozen and implemented only after all of the following gates are satisfied:

1. The terminal definitions and precedence rules are reviewed and accepted, including the non-collapse rule for UNRESOLVED.
2. The authoritative semantic field, schema versioning, validation, compatibility, and transition behavior are specified and approved.
3. Legacy outputs are classified with explicit migration logic, including non-mechanical cases for `false`, `ERROR`, and infrastructure failures.
4. The relationship between semantic terminals and process exit statuses is specified without making exit codes protocol semantics.
5. Evidence, rules, provenance, integrity, and mandatory-precondition requirements are enumerated sufficiently for independent implementation.
6. Verifier A and Verifier B have independently reviewable decision paths; Verifier B does not call or import Verifier A's decision function.
7. Altered-evidence detection and reproducibility tests are defined, including tests that distinguish FAIL from FAIL_CLOSED and UNRESOLVED.
8. A migration plan identifies compatibility behavior, receipt handling, version boundaries, rollout, and rollback without silently changing existing schemas.
9. Review confirms that implementation authorization is separate from approval of this boundary document.

Until every applicable gate is met and implementation is separately authorized, this document remains a draft boundary only.

## 10. Non-goals

This document does not provide or authorize:

- Any HD data.
- Any scientific truth claims.
- Any FPGA authorization.
- Any replacement of existing schemas yet.
- Any modification to the existing verifier, schemas, Makefile, or `SCIENTIFIC_OVERVIEW.md`.

STATUS: DRAFT — MIGRATION BOUNDARY — IMPLEMENTATION NOT AUTHORIZED
