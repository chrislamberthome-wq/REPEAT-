# Overview

REPEAT is a deterministic verification protocol that converts arbitrary processes into independently verifiable events.

## Purpose

The framework addresses a fundamental problem in modern computational and scientific systems: how to ensure that complex processes are deterministic, auditable, and free of silent errors.

By introducing deterministic canonicalization, receipt generation, and replayable verification, REPEAT enables transformation events to produce certification artifacts that can be checked independently of the originating system.

## Core Principles

### Deterministic Verification

Any event produces a receipt deterministically from inputs and transformation metadata. Given the same inputs, the verifier always emits the same receipt.

### Fail-Closed Enforcement

All operations must resolve to a binary outcome: PASS or FAIL. The verifier emits no certified receipt unless all declared invariants pass and all declared schemas validate.

### Replayable Audit Traces

Transformation steps generate artifacts that can be independently checked for correctness by third parties. Traces are deterministic JSONL sequences that capture every material step.

### Semantic Containment

The site invariant layer (SITE-INV-01) certifies that content projected to the built site is a faithful semantic subset of the canonical source documents. No significant token in a source document may be absent from its corresponding HTML projection.

## Invariant Stack

The invariant system is organized into distinct layers:

- **SITE-INV-01** — semantic containment: source tokens are a subset of projected tokens
- **SITE-INV-02** — reproducibility: identical inputs produce identical outputs
- **SITE-INV-03** — identity and provenance: artifacts are traceable to their declared origin
- **SITE-INV-04** — fail-closed enforcement: the verifier emits no receipt unless all invariants pass

## Release Governance

A separate policy layer (SITE-POL) governs release process admissibility:

- **SITE-POL-01** — release tag must be annotated
- **SITE-POL-03** — working tree must be clean at certification time
- **SITE-POL-04** — release artifacts must include receipt and manifests

The invariant layer answers: *is this artifact true?*
The policy layer answers: *was this release process admissible?*

## Status

This implementation is an experimental research protocol. The framework is under active development.
