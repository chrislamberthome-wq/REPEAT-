# Schema Governance Policy

## Purpose

The schema `schemas/repo-reference.schema.json` defines a repository contract that is enforced through automated verification.  
This document defines the governance rules controlling changes to that schema.

The goal is to ensure that the schema remains:

- deterministic
- auditable
- tamper-detectable
- explicitly versioned through review

## Verification Controls

The repository enforces four verification layers.

1. Schema Syntax Validation

`tests/test_schema_validation.py` verifies that the schema itself is valid under JSON Schema Draft 2020-12 using:

Draft202012Validator.check_schema()

2. Contract Conformance Tests

`tests/test_repo_reference_examples.py` validates example payloads to ensure the schema enforces the intended contract.

Tests include:

- minimal valid payload
- invalid enum value
- missing required field

3. Schema Integrity Lock

`tests/test_schema_fingerprint.py` computes the SHA-256 digest of:

schemas/repo-reference.schema.json

and compares it to a pinned expected digest.

This test detects any modification to the schema file.

4. CI Enforcement

The Makefile exposes explicit verification targets:

test-schema  
test  
ci

The `ci` target runs the schema validation before the broader test suite.

CI must pass before any merge.

## Schema Modification Rules

Any change to `schemas/repo-reference.schema.json` must follow these steps:

1. Modify the schema.
2. Recompute the SHA-256 digest.
3. Update `EXPECTED_SHA256` in `tests/test_schema_fingerprint.py`.
4. Update example vectors in `tests/test_repo_reference_examples.py` if the contract changes.
5. Ensure all tests pass.

A schema change that does not update the fingerprint test is considered invalid.

## Review Requirements

Schema changes require explicit code review.

Reviewers must confirm:

- the schema change is intentional
- example tests reflect the new contract
- the fingerprint update matches the modified schema
- CI passes

## Design Principle

The schema is treated as a controlled contract artifact.

All changes must be:

- explicit
- reviewable
- detectable through automated verification