# TMP v1 — Normative Specification

**Document**: `docs/TMP_SPEC.md`
**Protocol**: TMP-v1
**Version**: 1.0
**Canonicalization**: tmp-c14n-v1
**Status**: Draft — certification gate established; pending first CERTIFY run

---

## 1. Scope

TMP (Tetrahedral Mesh Protocol) v1 is a topology-first, fail-closed protocol
for representing and verifying tetrahedral mesh structures. The authoritative
object is a finite combinatorial structure, not a geometric embedding.

### 1.1 Non-goals

- TMP v1 does **not** define rendering, simulation, or physical embedding.
- TMP v1 does **not** certify floating-point geometry.
- TMP v1 does **not** support non-tetrahedral cells (hexahedra, prisms, etc.).
- TMP v1 does **not** define cross-mesh operations (union, intersection, etc.).
- TMP v1 does **not** require vertex coordinates to be present.

---

## 2. Object Model

### 2.1 The Three Layers

| Layer              | Role                         | Authoritative |
|--------------------|------------------------------|---------------|
| Combinatorial      | Incidence structure          | **Yes**       |
| Canonicalization   | Deterministic byte identity  | **Yes**       |
| Geometric          | Optional coordinate embedding | No            |

### 2.2 Top-Level Fields

| Field                    | Type     | Required | Description                                     |
|--------------------------|----------|----------|-------------------------------------------------|
| `protocol`               | string   | Yes      | Constant `"TMP-v1"`                             |
| `version`                | string   | Yes      | Constant `"1.0"`                                |
| `mesh_id`                | string   | Yes      | Unique identifier for this mesh object          |
| `vertex_ids`             | string[] | Yes      | Ordered list of vertex label identifiers        |
| `tetrahedra`             | object[] | Yes      | List of tetrahedron records                     |
| `adjacency`              | object[] | Yes      | Explicit interior face-sharing relations        |
| `boundary_faces`         | object[] | Yes      | Explicit exterior (boundary) face records       |
| `orientation_rule`       | string   | Yes      | Orientation convention (must be `"right_hand_sorted"`) |
| `canonicalization_version` | string | Yes      | Canonicalization spec version (`"tmp-c14n-v1"`) |
| `declared_invariants`    | object   | Yes      | Declared mesh properties including `canonical_sha256` |
| `geometry`               | object   | No       | Optional vertex coordinates; excluded from topology hash |

### 2.3 Tetrahedron Record

```json
{ "tetra_id": "T0", "vertices": ["v0", "v1", "v2", "v3"] }
```

- `tetra_id`: Non-empty string uniquely identifying the tetrahedron.
- `vertices`: Exactly 4 vertex ID strings; all must appear in `vertex_ids`;
  all 4 must be distinct.

### 2.4 Face Reference

```json
{ "tetra_id": "T0", "face": 2 }
```

- `tetra_id`: Must reference a declared tetrahedron.
- `face`: Integer in `[0, 3]`. Face `i` is the triangle **opposite** vertex
  index `i` in the `vertices` array.

Face vertex mapping for tetra `(v0, v1, v2, v3)`:

| Face index | Vertices (local order) | Opposite vertex |
|------------|------------------------|-----------------|
| 0          | v1, v2, v3             | v0              |
| 1          | v0, v2, v3             | v1              |
| 2          | v0, v1, v3             | v2              |
| 3          | v0, v1, v2             | v3              |

### 2.5 Adjacency Record

```json
{
  "left":  { "tetra_id": "T0", "face": 2 },
  "right": { "tetra_id": "T1", "face": 0 }
}
```

Declares that the face `face` of `left.tetra_id` shares a triangular surface
with face `face` of `right.tetra_id`. Both face references must point to the
same vertex set. The vertex orderings must be consistent with
`orientation_rule` (see §4).

### 2.6 Declared Invariants

```json
{
  "declared_invariants": {
    "canonical_sha256": "65927fea...",
    "vertex_count": 4,
    "tetra_count": 1,
    "adjacency_count": 0,
    "boundary_face_count": 4
  }
}
```

`canonical_sha256` is **required**. Count fields are optional but verified if
present.

---

## 3. Invariants

The following invariants are enforced by the verifier on every PASS verdict:

1. Each tetrahedron has exactly 4 **distinct** vertex IDs, all declared in
   `vertex_ids`.
2. No two tetrahedra have the same normalized (sorted) vertex set.
3. Each adjacency record references valid, declared tetra/face pairs.
4. No face slot appears in more than one adjacency or boundary record.
5. Every interior face (vertex set shared by exactly two tetra) appears in
   exactly one adjacency record.
6. Every boundary face (vertex set belonging to exactly one tetra) appears in
   exactly one boundary record.
7. Shared faces have consistent orientation (see §4).
8. The declared `canonical_sha256` matches the computed topology hash
   (see `docs/CANONICALIZATION.md`).
9. All declared count invariants match actual mesh dimensions.

---

## 4. Orientation Rule: `right_hand_sorted`

### 4.1 Convention

For tetra `T = (v0, v1, v2, v3)` with vertices in the order declared in the
`vertices` array, the local outward orientation of face `i` is determined by
the right-hand rule applied to the ordered vertices of that face.

### 4.2 Consistency Check

For two tetrahedra `T_left` and `T_right` sharing a face (declared in
`adjacency`):

- Compute `A = face_ordered_vertices(T_left, face_left)`: the face vertices
  of `T_left` in their local tetra order (excluding the opposite vertex).
- Compute `B = face_ordered_vertices(T_right, face_right)`: similarly for
  `T_right`.
- The face is **orientation-consistent** if and only if `B` is a reverse
  cyclic permutation of `A`.

A *reverse cyclic permutation* of `(a, b, c)` is any of:
`(c, b, a)`, `(b, a, c)`, `(a, c, b)`.

### 4.3 Canonical Orientation

During canonicalization, vertex IDs within each tetra are sorted
lexicographically. This removes local ordering information from the
topology hash; orientation consistency is verified separately at
check 8.

---

## 5. Verdict Semantics

| Verdict | Verifier exit | Meaning                                              |
|---------|---------------|------------------------------------------------------|
| PASS    | 0             | All invariants hold; canonical hash matches           |
| FAIL    | 1             | One or more structural/topological checks failed      |
| ERROR   | 2             | Runtime error: unreadable file, JSON parse failure,   |
|         |               | or non-object input                                  |

The verdict set is **exactly** `{PASS, FAIL, ERROR}`. No other verdicts are
defined in TMP v1.

---

## 6. Canonicalization

See `docs/CANONICALIZATION.md` for the complete normative rules.

Summary:

- Serialize a topology projection (geometry excluded) as compact UTF-8 JSON
  with sorted keys.
- The topology projection includes: `mesh_id`, `canonicalization_version`,
  `orientation_rule`, `vertex_ids` (sorted), `tetrahedra` (normalized and
  sorted), `adjacency` (normalized and sorted), `boundary_faces` (sorted).
- Compute `SHA-256` of the resulting bytes.
- Store as a 64-character lowercase hex string in
  `declared_invariants.canonical_sha256`.

---

## 7. Receipt Format

The reference verifier emits a minimal deterministic receipt:

```json
{
  "protocol": "TMP-v1",
  "mesh_id": "example",
  "vertex_count": 4,
  "tetra_count": 1,
  "adjacency_count": 0,
  "boundary_face_count": 4,
  "canonical_sha256": "65927fea...",
  "verdict": "PASS"
}
```

On FAIL or ERROR, an `"errors"` array is appended with human-readable
diagnostic messages.

---

## 8. Schema

The normative JSON Schema is `schemas/tmp_mesh.schema.json`.

---

## 9. Reference Verifier

`verifier/verify_tmp_mesh.py` is the normative reference implementation.

Usage:

```
python verifier/verify_tmp_mesh.py <mesh.json>
```

Exit codes: `0` = PASS, `1` = FAIL, `2` = ERROR.

---

## 10. Certification Gate

`scripts/certify_tmp_v1.py` runs the full certification gate and emits the
`TMP_CERT_CHECKLIST` and `TMP_CERT_DECISION`. See
`docs/TMP_CERTIFICATION_RULES.md` for post-certification policy.
