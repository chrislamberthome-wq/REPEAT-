ADR-0001: REPEAT_CORE authority and receipt precedence

* Status: PROPOSED
* Date: 2026-09-20

Decision question

What artifact establishes REPEAT_CORE_v1 authority, and what receipt schema—if any—has precedence for core verification?

1. Context

This repository contains multiple artifacts that plausibly participate in core verification, governance, or canonical specification, including:

* governance materials
* schema/ and schemas/ directories
* spec/ and documentation folders
* receipt- or verification-related files and directories
* a REPEAT_CORE_v1 naming reference in the project language

The decision question is not whether these artifacts exist, but which one is authoritative for the core definition and which receipt schema, if any, is binding when the repository must decide whether a core verification event is valid.

This ADR is intentionally narrow. It does not implement or define an event schema, receipt extension, or executable verification path. It only records the authority question and the evidence needed to resolve it.

The repository’s current state does not yet provide a single, explicit “this artifact is supreme” statement for REPEAT_CORE_v1. Without that, we must avoid inventing authority by inference alone.

2. Observed repository state

At the present repository state, the following observations are relevant:

* The repository root includes governance, spec/, schema/, schemas/, and related documentation directories.
* There is no clearly labeled, canonical “REPEAT_CORE_v1 authority” artifact that states: “this is the definitive source of REPEAT_CORE_v1.”
* There is no repository-level document that explicitly declares precedence between:
    * a core specification artifact,
    * a schema artifact,
    * a receipt artifact,
    * and an implementation artifact.
* The repository does not currently show a committed event schema with the authority to define core verification semantics.
* The repository does not currently show a receipt-schema extension that is explicitly declared to override or supersede other receipt definitions.
* The repository does not currently show an implementation artifact that is accepted as the canonical source of truth for core verification behavior.

In other words, the current repository state is consistent with an unresolved governance gap: it contains potential authority candidates, but not a proven precedence chain.

3. Authority candidates

The following candidates are plausible authority sources for REPEAT_CORE_v1:

1. REPEAT_CORE_v1 itself

* If an artifact is named REPEAT_CORE_v1 and is materially defined as the canonical version, that artifact is a candidate for supreme authority.
* However, the repository does not currently show a definitive governing statement that makes this artifact authoritative.

2. Specification documents

* Files such as SPEC.md, spec/, or related project documentation may define the semantics of the core.
* These are strong candidates for normative meaning, but only if they are explicitly declared authoritative.

3. Governance documents

* Governance or repository-policy files may establish decision-making authority and precedence.
* These are relevant to governance, but they are not sufficient by themselves unless they explicitly bind REPEAT_CORE_v1 and receipt precedence.

4. Schema artifacts

* schema/ and schemas/ directories may define canonical structure.
* A schema can define valid structure, but a schema is not automatically the governing source of truth for authority unless there is a document or governance statement establishing that status.

5. Receipt artifacts

* Receipt-related files may define evidence, verification, or reporting semantics.
* Receipts are not a source of authority over the core definition unless a higher-level authority explicitly states so.

6. Implementation artifacts

* Code, scripts, validators, and verification logic may reflect de facto behavior.
* Implementation is evidence of current practice, not necessarily legal or normative authority, unless the repository intentionally adopts it as binding.

4. Receipt-schema candidates

The following are plausible candidates for precedence in receipt handling:

1. No receipt schema

* If no receipt schema exists, then there is no schema-based precedence to establish.
* This is a valid and documentable stopping point.

2. A repository schema definition

* A canonical schema file may define the baseline structure for receipt records.
* It may be relevant for validation but not necessarily authoritative over all verification contexts.

3. A receipt extension or derived schema

* A receipt extension could be introduced to add fields or semantics beyond the base schema.
* Such an extension only has precedence if a governing document declares it as normative.

4. Implementation-defined receipt behavior

* If code interprets or emits receipts in a specific way, that behavior may be operationally relevant.
* But implementation behavior alone is not sufficient to establish receipt precedence without an explicit authority statement.

5. Event schema as a sibling source

* If an event schema exists, it may define events that are used to validate or describe receipt state.
* However, it is not automatically the governing source for receipt precedence unless the repository declares it so.

5. Decision criteria

The following criteria are required before making any authority or precedence decision:

1. Explicit naming of the authoritative artifact
    * The repository must state which artifact establishes REPEAT_CORE_v1 authority.
2. Explicit precedence statement
    * The repository must state whether any receipt schema takes precedence over other artifacts for core verification.
3. Evidence of normative intent
    * A document, policy, or governance statement must indicate that a candidate is binding, not merely present.
4. Consistency across artifacts
    * The authority candidate and receipt precedence claim must be consistent with specs, schema files, and any implementation or validation behavior.
5. Traceability
    * There must be a clear path from the authority claim to the verification logic or schema definitions.
6. No implied authority from absence
    * The absence of a schema or implementation cannot be treated as a silent decision in favor of another artifact.

6. Proposed authority model

The proposed authority model is intentionally conservative:

* REPEAT_CORE_v1 is not treated as authoritative merely because the name appears in the repository.
* Any authority claim must be backed by an explicit artifact or governing document.
* Receipt schema precedence is not assumed.
* In the current repository state, no artifact has sufficient evidence to establish precedence.

Therefore, the only defensible authority model at this time is:

* No authoritative artifact has been established for REPEAT_CORE_v1.
* No receipt schema has been established as having precedence for core verification.
* The repository must remain in a gated state until the required evidence exists.

This means the ADR does not resolve the question by making a false decision. Instead, it records the unresolved condition explicitly.

7. Consequences

If this ADR remains in the current state:

* The repository will not claim a binding authority source for REPEAT_CORE_v1 without evidence.
* The repository will not claim a receipt schema has precedence without explicit governance.
* The project avoids a false sense of completeness or canonical certainty where no authoritative artifact exists.
* Documentation remains honest about the current governance gap.
* Future work can proceed only once explicit evidence is produced.

If the repository later supplies the required evidence:

* The status can be updated from PROPOSED to ACCEPTED only after the evidence satisfies the gate defined below.
* A specific authority artifact may then be declared.
* A specific receipt schema may then be declared to take precedence, if appropriate.

8. Unresolved questions

The following questions remain unresolved and must be answered before any ACCEPTED authority decision is possible:

1. Which artifact is the canonical source of REPEAT_CORE_v1?
2. Is the canonical source a spec, a governance document, a schema, a named model, or a combination?
3. Does a receipt schema exist at all?
4. If a receipt schema exists, does it have binding precedence over other core artifacts?
5. If event schemas and receipt schemas are both present, which one governs verification order and semantic validity?
6. Is implementation behavior binding, or merely descriptive?
7. Does the repository need a dedicated governance artifact to declare core authority?
8. What evidence would be acceptable to establish precedence under audit review?

9. Explicit non-decisions

This ADR explicitly does not decide the following:

* It does not declare REPEAT_CORE_v1 to be authoritative merely because the name exists.
* It does not assign precedence to a schema directory just because it exists.
* It does not assign precedence to receipts just because they are present.
* It does not treat implementation behavior as normative without explicit repository approval.
* It does not assume that the absence of a schema or implementation implies a valid default authority.
* It does not create an event schema.
* It does not create a receipt-schema extension.
* It does not modify REPEAT_CORE_v1.
* It does not write implementation code.

This ADR is limited to a documentation decision about authority and precedence, not to the engineering design of the system itself.

10. Required evidence before status can become ACCEPTED

The status must remain PROPOSED until the following evidence is present:

1. A single artifact is explicitly designated as the canonical source of REPEAT_CORE_v1.
2. That artifact states or references the governance rule establishing authority.
3. A receipt schema, if any, is explicitly named as having precedence for core verification.
4. The precedence relationship is described in a repository document, not merely implied by folder structure or naming conventions.
5. Any implementation behavior is consistent with the declared authority and precedence.
6. A reviewer can trace the authority chain from:
    * the governing artifact,
    * to the core definition,
    * to the receipt schema,
    * to the verification behavior.

If any of the above is absent, the repository should not advance the status beyond PROPOSED.

Decision

Status: PROPOSED

The current repository state does not provide sufficient evidence to establish a valid authority chain for REPEAT_CORE_v1 or a binding receipt-schema precedence rule.

Therefore:

STATUS = UNRESOLVED

This is not a failure to decide; it is a deliberate refusal to fabricate authority without evidence.

UNRESOLVED
    ↓
NO EVENT SCHEMA
    ↓
NO RECEIPT EXTENSION
    ↓
NO IMPLEMENTATION

This gate exists to preserve an auditable reason for stopping. It prevents the repository from silently drifting from an unresolved authority question into a de facto but undocumented decision.

Audit note

This ADR is intentionally conservative and additive. It does not claim authority where none is demonstrated, and it does not create a synthetic precedence model where the repository lacks the necessary artifacts. The ADR is a record of the current evidence state, not a replacement for the missing governance evidence itself.

Commit target: adr/repeat-core-authority-receipt-precedence
File: docs/architecture/ADR-0001-REPEAT_CORE_AUTHORITY_AND_RECEIPT_PRECEDENCE.md

No other repository files should be changed in this commit.