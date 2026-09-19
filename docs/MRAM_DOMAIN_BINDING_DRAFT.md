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

This draft also fixes two domain decisions for this MRAM binding:

1. `C` is evaluated per run. The proposition is evaluated for each run in its local run context rather than as a cross-run aggregate.
2. `E` is assumed to be ordered, sequential, and gap-free for this MRAM domain. Evidence outside that ordering and continuity is outside the admitted domain for this binding.

A binding MUST therefore distinguish at least:

1. evidence and rules that satisfy the eventual admission and mandatory-precondition requirements;
2. evidence that is admitted and supports evaluation of the declared baseline and mandatory drift condition; and
3. the resulting Boolean proposition evaluation.

No implementation convention is normative merely because the current simulator or receipt layout happens to use it.

## 3. Explicit open bindings

The following items remain **`[DOMAIN-SPECIFIC — UNDEFINED]`** pending an approved MRAM domain binding, except where this draft explicitly resolves the decision above.

### 3.1 Baseline-value validity

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether a zero baseline is valid, and how a baseline that is unavailable is classified. The binding MUST distinguish a valid zero value from an unavailable or otherwise unusable baseline rather than relying on an implicit division or default-value convention.

### 3.2 Exact sufficiency count

For this MRAM domain, sufficiency is evaluated per run. The predicate is applied to the evidence set associated with a single run under the local run context, not to a cross-run aggregate. The run-level evidence is the ordered, sequential, gap-free observation stream admitted for that run.

### 3.3 Current-observation semantics

For this MRAM domain, “current” means the observation corresponding to the run currently being evaluated under `C`. The current run is assessed in sequence using the ordered evidence stream for that run. No global “first post-baseline” or “latest observation” convention is assumed by this binding.

### 3.4 Drift semantics

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether drift is signed or absolute, and how the resulting drift relates to the declared tolerance. The binding MUST specify the operator, reference value, units, comparison relation, and boundary behavior without inferring them from an existing metric name or simulator implementation.

### 3.5 Evidence structure

For this MRAM domain, `E` is assumed to be ordered, sequential, and gap-free. Evidence that is reordered, duplicated, missing, or non-monotonic is outside the admitted domain of this binding. Such evidence makes `Admissible(E,R)` false instead of yielding a special runtime predicate value or an implementation-specific fallback.

### 3.6 Binding versioning

**`[DOMAIN-SPECIFIC — UNDEFINED]`** Whether the MRAM domain-binding version is incorporated into canonical `R`, and therefore into canonical representation and any dependent integrity/provenance commitments. This draft does not assume that a version is included or excluded.

## 4. Non-inferences and review labels

The following are intentionally not asserted by this draft beyond the decisions fixed above:

- that a current observation is the first post-baseline observation;
- that a current observation is the latest observation;
- that the simulator’s baseline-window behavior is the normative MRAM definition;
- that a zero baseline is invalid or valid;
- that drift is absolute or signed;
- that the MRAM binding version is or is not part of canonical `R`.

Review classification for this draft:

- **PASS:** The Boolean-only nature of `Sufficient`, the separation of admission from evaluation, the requirement for evidence capable of establishing the declared baseline and evaluating mandatory drift, the per-run evaluation rule, the ordered/sequential/gap-free evidence assumption, and the stated terminal consequences follow from the frozen calculus.
- **OPEN:** Baseline-value validity, drift semantics, and binding versioning remain genuinely domain-specific and unresolved.
- **NACK:** Any reading that treats `[DOMAIN-SPECIFIC — UNDEFINED]` as a runtime predicate result, or that promotes an unbound observation-selection convention into the normative MRAM definition, contradicts the frozen boundary.

## 5. Non-freezing boundary

This inline draft does not select the remaining open bindings, amend the master calculus, authorize implementation, or modify existing schemas or verifier behavior. A later approved binding MUST resolve the remaining open items before a fully bound `Sufficient(E,C,R)` or an implementation-specific MRAM verifier claims to be normative.
