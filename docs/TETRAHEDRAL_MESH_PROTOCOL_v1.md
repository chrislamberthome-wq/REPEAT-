# TETRAHEDRAL_MESH_PROTOCOL_v1.md

**Status:** Draft v1.0

---

## Purpose

The Tetrahedral Mesh Protocol (TMP) defines a deterministic method for encoding, measuring, and verifying geometric state using tetrahedral meshes.

The protocol enables geometric substrates (Platoputer systems) to produce REPEAT-verifiable receipts by canonicalising tetrahedral state and validating structural invariants.

The tetrahedron is chosen because it is the minimal rigid volumetric primitive in three-dimensional space.  Complex geometries can be decomposed into tetrahedral meshes while preserving deterministic verification properties.

---

## 1. Terminology

| Term        | Definition                                                     |
|-------------|----------------------------------------------------------------|
| Vertex      | A point in 3D space identified by a canonical ID               |
| Edge        | Connection between two vertices                                |
| Face        | Triangular surface formed by three vertices                    |
| Cell        | A tetrahedron composed of four vertices                        |
| Mesh        | Collection of tetrahedral cells                                |
| Orientation | Signed ordering of vertices defining handedness                |
| Invariant   | A property that must remain valid for a mesh state             |

---

## 2. Canonical Fields

All tetrahedral cells **MUST** serialise fields in deterministic order.

```json
{
  "mesh_id": "string",
  "cells": [
    {
      "cell_id": "string",
      "vertex_ids": ["v1", "v2", "v3", "v4"],
      "vertices": {
        "v1": [0, 0, 0],
        "v2": [1, 0, 0],
        "v3": [0, 1, 0],
        "v4": [0, 0, 1]
      },
      "edges": [
        ["v1", "v2"], ["v1", "v3"], ["v1", "v4"],
        ["v2", "v3"], ["v2", "v4"], ["v3", "v4"]
      ],
      "faces": [
        ["v1", "v2", "v3"], ["v1", "v2", "v4"],
        ["v1", "v3", "v4"], ["v2", "v3", "v4"]
      ],
      "orientation": "positive",
      "volume": 0.166666
    }
  ]
}
```

### Canonicalisation Rules

- Vertex IDs **MUST** be sorted lexicographically.
- Edge pairs **MUST** be sorted (smaller ID first); the edge list **MUST** be sorted.
- Face triples **MUST** be sorted; the face list **MUST** be sorted.
- Vertex coordinates **MUST** be serialised with fixed decimal precision (10 places).
- JSON keys **MUST** be lexicographically sorted.
- Encoding **MUST** be UTF-8.

---

## 3. Mesh Invariants

The verifier **MUST** evaluate the following invariants.

### 3.1 Structural Validity

Each tetrahedral cell **MUST** satisfy:

- exactly 4 vertices
- exactly 6 edges
- exactly 4 faces

### 3.2 Edge Consistency

All edges **MUST** correspond to valid vertex pairs present in `vertex_ids`.

### 3.3 Face Orientation

Declared `orientation` **MUST** match the sign of the computed signed volume.

### 3.4 Signed Volume

Signed volume **MUST** be non-zero (|V| > `VOLUME_TOLERANCE = 1e-9`).

```
V = det(v2-v1, v3-v1, v4-v1) / 6
```

If `|V| ≤ VOLUME_TOLERANCE` → **FAIL** (degenerate tetrahedron).

### 3.5 Adjacency Consistency

Neighbouring cells sharing a face **MUST** reference identical vertex triples.

---

## 4. Geometric Encoding Model

A Platoputer implementation **MAY** encode information using:

| Element | Encodable State    |
|---------|--------------------|
| Vertex  | activation state   |
| Edge    | length class       |
| Face    | orientation        |
| Cell    | volume class       |
| Mesh    | topology           |

Binary requests transform mesh states.

**Example transformation:**

```
binary_input → edge_state_map → geometric transformation
```

The resulting geometry becomes the observable state.

---

## 5. Measurement and Canonicalisation

Sensors or measurement systems produce observed geometry.

Observed geometry **MUST** be normalised before verification.

Normalisation includes:

- coordinate precision rounding
- vertex ordering normalisation
- tolerance thresholds

---

## 6. Receipt Schema

Every verification emits a TMP receipt conforming to `receipts/tetra_mesh_receipt.schema.json`.

```json
{
  "receipt_type": "tetra_mesh_verification",
  "mesh_id": "string",
  "cell_count": 1024,
  "timestamp": "2024-01-01T00:00:00Z",
  "canonical_hash": "<sha256-hex>",
  "prev_receipt_hash": "<sha256-hex-or-null>",
  "verifier_version": "tmp_v1",
  "result": "PASS"
}
```

### Hash Computation

```
canonical_hash = SHA256(canonical_json(mesh_state))
```

Derived fields **MUST** be excluded during hashing.

---

## 7. PASS / FAIL Rules

Verification outcomes follow deterministic rules.

### PASS

All invariants satisfied:

- structural validity
- orientation consistency
- adjacency correctness
- non-zero volumes

### FAIL

Any invariant violated.

Examples:

- degenerate tetrahedron
- broken adjacency
- edge mismatch
- orientation conflict
- declared volume does not match computed volume

### ERROR

Processing failure.

Examples:

- malformed JSON
- missing required fields
- unsupported version

---

## 8. REPEAT Integration

TMP integrates into the REPEAT framework as a geometric verification layer.

**Pipeline:**

```
binary_request
      ↓
platoputer_geometry
      ↓
measurement
      ↓
canonicalisation
      ↓
tmp_verifier
      ↓
repeat_receipt
```

Each verification produces:

```
audit.jsonl
receipt.json
trace.jsonl
```

All records **MUST** be replay-verifiable.

---

## 9. Security Properties

### Determinism

Canonicalisation ensures identical geometry produces identical hashes.

### Local Error Detection

Errors are detectable at the tetrahedral cell level.

### Global Integrity

Mesh state can be replay-verified.

### Tamper Evidence

Any modification alters the canonical hash.

---

## 10. Non-Goals

TMP does **NOT** attempt to:

- optimise mesh generation
- perform physics simulation
- enforce geometric compression

The protocol only defines verification semantics.

---

## 11. Future Extensions

Potential extensions include:

- hierarchical meshes
- multi-resolution verification
- optical sensing integration
- cryptographic signing of receipts
- PlatoBench: canonical tetrahedral decompositions of all five Platonic solids

---

## Summary

The Tetrahedral Mesh Protocol provides a deterministic geometric substrate for REPEAT-verified systems.

The tetrahedron serves as the minimal volumetric primitive enabling:

- rigid geometry
- deterministic canonicalisation
- local and global verification
- auditable transformation receipts

This establishes geometry as a verifiable computational medium.

```
Triangle is the verifier of surface.
Tetrahedron is the verifier of volume.
REPEAT is the verifier of the verifier.
```
