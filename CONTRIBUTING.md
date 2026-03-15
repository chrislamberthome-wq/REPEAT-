# Contributing to REPEAT

## Overview

REPEAT is a deterministic verification framework designed to enforce contract integrity through schema validation, golden vectors, fingerprint locking, and fail-closed CI verification.

The goal of the project is to make verification artifacts reproducible, auditable, and portable across systems.

## Development Setup

Clone the repository and install dependencies:

```bash
pip install -r requirements.txt
```

Run the verification suite:

```bash
pytest
make ci
```

All contributions must pass CI before review.

## Project Principles

REPEAT follows several engineering constraints:

- Deterministic behavior
- Fail-closed validation
- Explicit contract artifacts
- No silent schema drift

Changes that introduce non-deterministic behavior or bypass verification gates will not be accepted.

## Repository Structure

- `schemas/`
  Contract definitions.

- `tests/`
  Validation tests, vectors, and fingerprint checks.

- `tests/vectors/`  
  Golden contract examples used for deterministic validation.

- `verifier/`
  External CLI validator for contract artifacts.

- `docs/`
  Governance and protocol documentation.

## Contribution Workflow

1. Fork the repository
2. Create a feature branch
3. Add or modify code
4. Run local verification

   ```bash
   pytest
   make ci
   ```

5. Submit a pull request

## First Contribution Ideas

Look for issues labeled:

- `good-first-issue`

Typical starter tasks include:

- adding new schema vectors
- improving verifier diagnostics
- expanding test coverage
- documentation improvements

## Governance

Schema modifications must follow the rules defined in:

`docs/SCHEMA_GOVERNANCE.md`

This includes updating the schema fingerprint and contract vectors when the schema changes.