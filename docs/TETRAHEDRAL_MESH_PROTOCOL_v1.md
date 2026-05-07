# Tetrahedral Mesh Protocol v1

**Protocol Version:** `tmp_v1`

## Overview

The Tetrahedral Mesh Protocol (TMP) defines a deterministic, reproducible
verification pipeline for tetrahedral mesh states. It produces a canonical
receipt that can be replayed, audited, and chained into larger workflows.

## Version Binding

All TMP touchpoints must bind to the same version string (`tmp_v1`):

| Touchpoint | Location | Value |
|---|---|---|
| Metadata constant | `verifier/tmp_metadata.py` → `TMP_VERSION` | `tmp_v1` |
| Verifier constant | `verifier/verify_mesh.py` → `VERIFIER_VERSION` | `tmp_v1` |
| Emitted receipt field | `verifier_version` in receipt JSON | `tmp_v1` |
| This document | `docs/TETRAHEDRAL_MESH_PROTOCOL_v1.md` | `tmp_v1` |

Any divergence between these touchpoints is a protocol error and must be
caught by the version-binding check in the test suite.

## Schemas

- **Mesh state input:** `schemas/tetra_mesh_state.schema.json`
- **Verification receipt:** `receipts/tetra_mesh_receipt.schema.json`

## Canonicalization Rules

1. All float values are quantized to 9 decimal places (round-half-up).
2. All dictionary keys are sorted lexicographically at every nesting level.
3. Within each cell, `vertex_ids` are sorted lexicographically.
4. Cells are sorted by `cell_id`.
5. The canonical bytes are produced by `json.dumps` with `sort_keys=True`,
   `separators=(",", ":")`, `ensure_ascii=False`, encoded as UTF-8.

These rules ensure that two semantically identical mesh states (differing only
in key order, vertex order, or float representations) produce identical
canonical bytes and therefore identical hashes.

## Exit-Code Contract

The CLI (`cli/verify_tetra_mesh.py`) follows this frozen exit-code contract:

| Code | Meaning |
|------|---------|
| `0`  | PASS — mesh verified successfully |
| `1`  | FAIL — mesh failed verification |
| `2`  | ERROR — runtime error (bad file, parse error, etc.) |

This contract is stable and must not change once TMP is integrated into CI
pipelines.

## Receipt Schema

A verification receipt contains the following deterministic fields:

| Field | Type | Description |
|---|---|---|
| `receipt_type` | string | Always `"tetra_mesh_verification"` |
| `mesh_id` | string | Identifier from the input mesh state |
| `cell_count` | integer | Number of cells verified |
| `canonical_hash` | string | SHA-256 hex of canonical JSON bytes |
| `verifier_version` | string | Version string (e.g. `tmp_v1`) |
| `result` | string | `PASS`, `FAIL`, or `ERROR` |
| `reasons` | array | List of failure reasons (empty on PASS) |
| `timestamp` | string | ISO-8601 UTC timestamp (non-deterministic) |

The `timestamp` field is non-deterministic and must be excluded from
golden-vector comparisons.

## Tamper Detection

Any modification to the mesh state after canonicalization will produce a
different `canonical_hash`, causing verification to fail if the hash is
compared against a frozen golden receipt.

## CI Certification Boundary

TMP is considered certified when all of the following hold in CI:

- Frozen vector artifacts are unchanged.
- Canonicalization produces stable bytes and hashes across equivalent inputs.
- Results are platform-independent across OS/Python matrix.
- Receipt schema remains stable and consistent.
- Tamper detection produces `FAIL`.
- Replay tests produce `PASS` deterministically.
- CLI behavior follows the exit-code contract above.
- Protocol version binding is consistent across all touchpoints.
