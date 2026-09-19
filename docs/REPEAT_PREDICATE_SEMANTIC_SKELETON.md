# REPEAT Predicate Semantic Skeleton Patch

## Status and disposition

This document patches the non-freezing semantic skeleton only. It records the accepted interpretation without amending the master calculus or authorizing implementation.

- **Reading A:** ACCEPT
- **Reading B:** REJECT
- **Amend master calculus:** NO
- **Patch skeleton:** YES
- **Implementation authorization:** NO

## Governing rule

**UNDEFINED has no runtime existence.** It is a documentation-only placeholder used by this non-freezing skeleton.

A fully bound `Sufficient(E,C,R)` **MUST** be a total Boolean decision procedure over its declared input domain and **MUST** return only `TRUE` or `FALSE`.

Any condition that a bound domain cannot deterministically resolve to `TRUE` or `FALSE` is not a third predicate result. It indicates that the input is outside the declared predicate domain or violates a required admission/precondition. It **MUST** therefore be handled upstream through `Admissible(E,R)` or, where applicable, through the separate verifier execution-failure path.

## Layer separation

The three layers remain distinct:

1. **`Admissible(E,R)`** — the admission/domain boundary. It determines whether the evidence and rules satisfy the requirements for predicate evaluation.
2. **`Sufficient(E,C,R)`** — a Boolean predicate only. Once fully bound and invoked on its declared domain, it returns exactly `TRUE` or `FALSE`; it never returns `UNDEFINED` or `UNRESOLVED`.
3. **`UNRESOLVED`** — a terminal produced by `¬Sufficient`, never by a third predicate value.

Conceptually:

```text
if not Admissible(E, R):
    handle upstream as an admission/domain failure or verifier execution failure
else:
    if Sufficient(E, C, R):
        continue with the TRUE branch
    else:
        produce UNRESOLVED
```

The pseudocode is a semantic skeleton, not implementation authorization.

## Contradictory evidence

Contradictory evidence has no special semantics at this layer. The eventual domain binding **MUST** specify whether contradiction:

- makes the input inadmissible;
- makes `Sufficient(E,C,R) = FALSE`; or
- is handled by another domain-specific rule.

That choice remains **`[DOMAIN-SPECIFIC — UNDEFINED]`** until binding. In particular, `UNDEFINED` records that the domain choice has not yet been supplied; it does not describe a runtime return value.

## Non-freezing boundary

This patch does not select a contradiction policy, define a concrete predicate domain, modify the master calculus, change existing verifier behavior, or authorize implementation. Those decisions require a later domain binding and separate implementation authorization.
