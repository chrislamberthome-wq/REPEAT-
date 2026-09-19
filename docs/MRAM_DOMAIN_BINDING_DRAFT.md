# MRAM Domain Binding — Inline Draft

## Status and disposition

This document is an inline, non-freezing domain-binding draft for the MRAM evidence model. It records consequences that follow from the frozen calculus while keeping unresolved domain choices explicit. It does not amend the master calculus, silently promote an implementation convention to a normative definition, change existing verifier behavior, or authorize implementation.

Status: **DRAFT — DOMAIN BINDING REVIEW — IMPLEMENTATION NOT AUTHORIZED**

## 1. Governing semantic boundary

`Sufficient(E,C,R)` is a Boolean predicate only. Once a domain binding is complete and the evidence is within its declared evaluation domain, it MUST return exactly `TRUE` or `FALSE`; it MUST NOT return `UNDEFINED` or `UNRESOLVED`.

`[DOMAIN-SPECIFIC — UNDEFINED]` is documentation of an unbound choice, not a runtime predicate result. If the evidence or rules cannot be admitted or evaluated under the eventual binding, that condition belongs at the `Admissible(E,R)` / mandatory-precondition boundary or the applicable verifier failure path. It MUST NOT be smuggled into the predicate as an additional truth value.

The terminal consequences remain those of the frozen calculus:

- failure of integrity, schema, parse, provenance, or mandatory preconditions prevents proposition evaluation and yields `FAIL_CLOSED`;
- admissible evidence that evaluates the proposition as supported yields `PASS`;
- admissible evidence that evaluates the proposition as unsupported yields `FAIL`;
- valid and admissible evidence that does not deterministically justify either proposition outcome may yield `UNRESOLVED`, subject to the frozen semantic model; and
- `UNRESOLVED` MUST NOT be silently collapsed into `FAIL` or converted to `PASS` by caller preference, a default branch, or an implementation convention.

## 2. Settled MRAM consequence

For this draft, **Sufficient requires evidence capable of establishing the declared baseline and evaluating the mandatory drift condition**.

This statement does not, by itself, define the observation selected as “current,” the exact observation count, the numerical drift operator, or the admissibility policy for malformed evidence. Those are domain-binding inputs that remain open below.

A binding MUST therefore distinguish at least:

1. evidence and rules that satisfy the eventual admission and mandatory-precondition requirements;
2. evidence that is admitted and supports evaluation of the declared baseline and mandatory drift condition; and
3. the resulting Boolean proposition evaluation.

No implementation convention is normative merely because the current simulator or receipt layout happens to use it.

## 3. Explicit open bindings

The following items remain **`[DOMAIN-SPECIFIC — UNDEFINED]`** pending an approved MRAM domain binding.

### 3.1 Baseline-value validity

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether a zero baseline is valid, and how a baseline that is unavailable is classified. The binding MUST distinguish a valid zero value from an unavailable or otherwise unusable baseline rather than relying on an implicit division or default-value convention.

### 3.2 Exact sufficiency count

**`[DOMAIN-SPECIFIC — UNDEFINED]`** The precise definition of the required `N` observations. This includes which observations count, whether the baseline observation(s) are included, and what makes the count sufficient for evaluation.

### 3.3 Current-observation semantics

**`[DOMAIN-SPECIFIC — UNDEFINED]`** The meaning of the “current” observation in the MRAM evidence model. The binding has not selected whether “current” is:

- exactly the first observation after the baseline;
- the latest observation;
- a specifically identified observation; or
- another observation selected under `R`.

This choice MUST remain unbound here. The normative domain definition MUST NOT assume the first, latest, or any other implementation convention until `R` explicitly binds it.

### 3.4 Drift semantics

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether drift is signed or absolute, and how the resulting drift relates to the declared tolerance. The binding MUST specify the operator, reference value, units, comparison relation, and boundary behavior without inferring them from an existing metric name or simulator implementation.

### 3.5 Evidence structure

**`[DOMAIN-SPECIFIC — UNDEFINED]`** The treatment of malformed, missing, reordered, duplicate, or non-monotonic observations. The binding MUST specify which cases make `Admissible(E,R)` false, which—if any—are evaluated as a proposition failure, and whether any case has another domain-specific disposition. No such case is a third value of `Sufficient`.

### 3.6 Binding versioning

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether the MRAM domain-binding version is incorporated into canonical `R`, and therefore into canonical representation and any dependent integrity/provenance commitments. This draft does not assume that a version is included or excluded.

## 4. Non-inferences and review labels

The following are intentionally not asserted by this draft:

- that a current observation is the first post-baseline observation;
- that a current observation is the latest observation;
- that the simulator’s baseline-window behavior is the normative MRAM definition;
- that a zero baseline is invalid or valid;
- that drift is absolute or signed;
- that malformed, reordered, duplicate, or non-monotonic evidence has a particular terminal; or
- that the MRAM binding version is or is not part of canonical `R`.

Review classification for this draft:

- **PASS:** The Boolean-only nature of `Sufficient`, the separation of admission from evaluation, the requirement for evidence capable of establishing the declared baseline and evaluating mandatory drift, and the stated terminal consequences follow from the frozen calculus.
- **OPEN:** The six bindings in Section 3 are genuinely domain-specific and remain undefined.
- **NACK:** Any reading that treats `[DOMAIN-SPECIFIC — UNDEFINED]` as a runtime predicate result, or that promotes an unbound observation-selection convention into the normative MRAM definition, contradicts the frozen boundary.

## 5. Non-freezing boundary

This inline draft does not select the six open bindings, amend the master calculus, authorize implementation, or modify existing schemas or verifier behavior. A later approved binding MUST resolve the open items before a fully bound `Sufficient(E,C,R)` or an implementation-specific MRAM verifier claims to be normative.
