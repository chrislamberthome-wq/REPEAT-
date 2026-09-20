ADR-0002: REPEAT_CORE authority and receipt precedence — decision preparation

Status: PROPOSED
Date: 2026-09-20
Decision Status: DECISION PREPARATION

Decision Question

What explicit artifact and governance rule should establish:

1. authoritative REPEAT_CORE_v1 scope and authority; and
2. receipt-schema precedence, if a receipt schema is to have normative precedence?

This ADR prepares that decision without resolving it.

⸻

Relationship to ADR-0001

ADR-0001 records that:

* no authoritative REPEAT_CORE_v1 artifact has been identified;
* no binding receipt-schema precedence rule has been identified;
* the authority question is UNRESOLVED;
* the receipt-precedence question is UNRESOLVED.

ADR-0002 does not supersede ADR-0001.

ADR-0002 does not convert the unresolved state into an implementation decision.

⸻

Current Evidence State

The repository evidence establishes:

* multiple specification, governance, schema, receipt, and implementation surfaces exist;
* no identified artifact explicitly establishes itself as the authoritative REPEAT_CORE_v1;
* no identified rule establishes precedence among the existing receipt-schema surfaces;
* existing documents explicitly preserve unresolved authority in relevant areas;
* the external-system boundary is documented separately and does not modify REPEAT_CORE_v1;
* the ADR-0001 branch contains only the ADR-0001 documentation change.

Therefore:

REPEAT_CORE_v1 AUTHORITY = UNRESOLVED
RECEIPT PRECEDENCE       = UNRESOLVED

No conclusion is derived from the absence of an authority declaration.

⸻

Decision Preparation Scope

The eventual governance decision must explicitly address the following.

A. Core Authority

The decision must identify, by exact repository path and immutable/versioned identity where applicable:

* the artifact that establishes REPEAT_CORE_v1;
* the normative scope of that artifact;
* the relationship between the core authority and other specifications;
* the relationship between the core authority and implementation;
* the mechanism by which future changes to the core authority are controlled.

An artifact must not become authoritative merely because it is named, referenced, older, more complete, or currently implemented.

B. Receipt Precedence

The decision must explicitly state whether:

* one existing receipt schema has precedence;
* a new canonical receipt schema will be established;
* receipt schemas remain non-authoritative siblings;
* or another explicitly defined governance arrangement applies.

If precedence is established, the decision must identify the exact governing rule and the affected artifacts.

No receipt schema acquires precedence by implication.

C. Relationship to Existing Artifacts

The eventual decision must establish how the selected authority, if any, relates to:

* existing specifications;
* governance documentation;
* existing receipt schemas;
* verifier implementations;
* domain-specific schemas;
* external-system specifications.

No existing artifact is promoted during this ADR.

⸻

Candidate Decision Structures

The following are decision structures for later evaluation, not selected outcomes.

Candidate A — Existing Artifact Becomes Explicit Authority

An existing repository artifact could be explicitly designated as the authoritative REPEAT_CORE_v1 artifact.

Required evidence would include:

* exact artifact identity;
* normative scope;
* explicit precedence rule;
* compatibility assessment against existing repository surfaces;
* traceability from authority to implementation.

Not selected.

Candidate B — Dedicated Core Authority Artifact

A new dedicated artifact could explicitly define the frozen REPEAT_CORE_v1 boundary and its precedence over subordinate artifacts.

Required evidence would include:

* exact normative boundary;
* explicit precedence relationship;
* versioning/freeze mechanism;
* relationship to existing specifications, schemas, receipts, and implementation;
* migration treatment for conflicting or duplicate surfaces.

Not selected.

Candidate C — Explicit Non-Precedence Model

The repository could explicitly preserve multiple non-authoritative artifacts while defining a separate mechanism for determining which claims are admissible for a particular verification operation.

Required evidence would include:

* explicit statement that no repository-wide receipt-schema precedence exists;
* deterministic selection rules where operational selection is required;
* prohibition on interpreting operational selection as normative authority;
* traceability requirements.

Not selected.

These candidates are illustrative decision structures only. Their presence does not constitute a ranking, recommendation, or decision.

⸻

Required Acceptance Evidence

Before the authority question can transition from UNRESOLVED, a future accepted decision must provide:

1. one explicitly identified authority model for REPEAT_CORE_v1;
2. an explicit statement of normative scope;
3. an explicit precedence relationship, or an explicit declaration that no such precedence exists;
4. explicit treatment of existing competing artifacts;
5. traceability sufficient to determine which artifact governs a verification claim;
6. consistency with the existing core boundary;
7. a documented migration or coexistence rule where existing artifacts remain;
8. evidence that the decision does not silently authorize implementation beyond the defined authority boundary.

Until those conditions are satisfied, the decision remains unresolved.

⸻

Non-Decisions

This ADR does not:

* designate an authoritative REPEAT_CORE_v1 artifact;
* designate a canonical receipt schema;
* establish receipt-schema precedence;
* create an event schema;
* extend a receipt schema;
* modify REPEAT_CORE_v1;
* modify existing verifier semantics;
* authorize implementation;
* authorize migration;
* authorize the external sensor/audio architecture to cross the core boundary.

⸻

Governance Gate

The repository remains gated as follows:

REPEAT_CORE_v1 AUTHORITY
        =
UNRESOLVED
RECEIPT PRECEDENCE
        =
UNRESOLVED
        ↓
NO EVENT SCHEMA
        ↓
NO RECEIPT EXTENSION
        ↓
NO CORE MODIFICATION
        ↓
NO IMPLEMENTATION

The external sensor/audio architecture remains conceptually specified but downstream-gated.

⸻

Decision Status

ADR-0001 = PROPOSED / UNRESOLVED
ADR-0002 = PROPOSED / DECISION PREPARATION
AUTHORITY = UNRESOLVED
RECEIPT PRECEDENCE = UNRESOLVED

No authority is inferred from absence.

No implementation authority is inferred from documentation.

No schema authority is inferred from existing usage.

No receipt precedence is inferred from repository structure.

⸻

Next Governance Transition

The next valid transition is an explicit governance decision supported by repository evidence and recorded in a subsequent accepted ADR or other explicitly governing artifact.

Until that transition occurs, this ADR is a preparation record only.
