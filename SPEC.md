REPEAT / B4IU / IDA — Normative Spec v0.1 (One Page, PDF-ready)

## REPEAT-Bounded Autotonomy

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human
micro-approval only within predeclared constraints and only if each step produces an auditable
trace and a verifier can NACK/fail-closed (non-zero exit / invalid receipt). This does not
claim self-governing goal sovereignty, moral agency, or rights—only autonomy of execution
under mandatory verification.

Implementation evidence: [`docs/autotonomy/IMPLEMENTATION_MAP.md`](docs/autotonomy/IMPLEMENTATION_MAP.md)

---

# TMP v1 — Tetrahedral Mesh Protocol, Version 1

## 1. Purpose and Scope

TMP v1 is a topology-first protocol for representing, canonicalizing, and verifying tetrahedral
meshes. The authoritative object is **combinatorial**: tetrahedra, vertices, adjacency, and
boundary faces. Geometric coordinates are optional metadata and play no role in verification.

The protocol is designed for deterministic, auditable verification with fail-closed semantics,
aligned with REPEAT-style principles.

### 1.1 Design Choices

| Choice | Value |
|--------|-------|
| Primary object | Combinatorial (topology) |
| Coordinates | Optional metadata only |
| Canonical identity | Derives from topology, not embedding |
| Verifier behavior | Fail-closed |
| Verdict set | `PASS` \| `FAIL` \| `ERROR` (exactly) |

### 1.2 Non-Goals

TMP v1 is **not**:
- A geometry standard. It does not define coordinate systems, units, or spatial transformations.
- A rendering or simulation format.
- A mesh generation or modification protocol.
- A floating-point comparison standard.
- A replacement for volume mesh formats (e.g., VTK, Gmsh).

---

## 2. Object Model

### 2.1 Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `protocol` | string | **yes** | Must be exactly `"TMP-v1"` |
| `version` | string | **yes** | Spec version, semver format (e.g. `"1.0.0"`) |
| `mesh_id` | string | **yes** | Non-empty unique identifier for this mesh |
| `vertex_ids` | array[string] | **yes** | Ordered list of at least 4 distinct vertex labels |
| `tetrahedra` | array[TetraRecord] | **yes** | At least 1 tetrahedron |
| `adjacency` | array[AdjacencyRecord] | **yes** | Explicit face-sharing records (may be empty) |
| `boundary_faces` | array[BoundaryFaceRecord] | **yes** | Explicit boundary face records |
| `orientation_rule` | string | **yes** | Must be `"right_hand_outward"` in TMP v1 |
| `canonicalization_version` | string | **yes** | Must be `"c14n-v1"` |
| `declared_invariants` | array[string] | **yes** | Invariant class names to enforce (may be empty) |
| `geometry` | object | no | Optional coordinate metadata (excluded from topology hash) |
| `topology_hash` | string | no | Pre-computed canonical hash for integrity checking |

### 2.2 TetraRecord

```json
{
  "tetra_id": "T0",
  "vertices": ["v0", "v1", "v2", "v3"]
}
```

- `tetra_id`: unique non-empty string identifier within the mesh.
- `vertices`: exactly 4 distinct vertex labels, ordered to define orientation.

### 2.3 AdjacencyRecord

```json
{
  "left":  { "tetra_id": "T0", "face": 2 },
  "right": { "tetra_id": "T1", "face": 0 }
}
```

- `left` and `right` are `FaceRef` objects with `tetra_id` (string) and `face` (integer 0–3).
- Declares that face `left.face` of tetrahedron `left.tetra_id` is shared with face
  `right.face` of tetrahedron `right.tetra_id`.
- Each `FaceRef` pair must share the same set of 3 vertices.

### 2.4 BoundaryFaceRecord

```json
{
  "tetra_id": "T0",
  "face": 3
}
```

- Declares that face index `face` of tetrahedron `tetra_id` is a boundary face (not shared
  with any other tetrahedron).

### 2.5 Face Index Convention

For a tetrahedron with `vertices = [v_a, v_b, v_c, v_d]` (0-indexed):

| Face index | Opposite vertex | Vertices of face |
|------------|----------------|-----------------|
| 0 | `v_a` (index 0) | `[v_b, v_c, v_d]` |
| 1 | `v_b` (index 1) | `[v_a, v_c, v_d]` |
| 2 | `v_c` (index 2) | `[v_a, v_b, v_d]` |
| 3 | `v_d` (index 3) | `[v_a, v_b, v_c]` |

Face `i` is the face **opposite** to vertex at position `i` in the vertex list.

### 2.6 Geometry Block (Optional)

```json
{
  "geometry": {
    "coordinate_system": "euclidean_3d",
    "coordinates": {
      "v0": [0.0, 0.0, 0.0],
      "v1": [1.0, 0.0, 0.0]
    }
  }
}
```

The `geometry` block is **excluded** from the topology hash. Its presence or absence does not
affect `PASS`/`FAIL`/`ERROR` verdict for topological checks.

---

## 3. Orientation Rule

The `orientation_rule` field MUST be `"right_hand_outward"` in TMP v1.

Under this convention:
- A tetrahedron `(v_a, v_b, v_c, v_d)` has positive orientation when
  `det([v_b - v_a, v_c - v_a, v_d - v_a]) > 0`.
- For a shared face between two tetrahedra, the cyclic ordering of the face vertices in the
  two tetrahedra MUST be reversed (one is a cyclic rotation of the other's reversal).

---

## 4. Invariant Classes

The `declared_invariants` array lists which topological properties the verifier MUST enforce.
An empty list means only structural checks (§5, checks 1–9) apply.

| Name | Description |
|------|-------------|
| `manifold_interior` | Every interior face is shared by exactly 2 tetrahedra (enforced structurally; declaring it is explicit) |
| `closed_boundary` | All boundary edges appear in exactly 2 boundary faces (closed surface) |
| `connected` | All tetrahedra are reachable from the first by adjacency traversal |
| `oriented` | Orientation consistency holds across all shared faces |

---

## 5. PASS / FAIL / ERROR Semantics

| Verdict | Exit Code | Meaning |
|---------|-----------|---------|
| `PASS` | 0 | All checks pass; canonical hash matches if declared |
| `FAIL` | 1 | A topological or structural invariant is violated |
| `ERROR` | 2 | Input cannot be processed (schema invalid, parse error, internal fault) |

### Fail-Closed Rule

If any check cannot be performed (missing field, type error, internal exception), the verdict
is `ERROR`. There is **no silent pass**. The verifier never returns `PASS` by default.

---

## 6. Verifier Check Order

Checks are ordered so that each later check depends on the earlier checks having passed:

1. **Schema validity** — required fields, correct types, known enum values.
2. **Distinct vertex references per tetrahedron** — all 4 vertices distinct and in `vertex_ids`.
3. **No duplicate tetrahedra** — no two tetras share the same 4-vertex set after normalization.
4. **Face accounting** — `|tetrahedra| × 4 = |adjacency| × 2 + |boundary_faces|`.
5. **Adjacency references valid** — each `tetra_id` in adjacency exists; `face` is 0–3.
6. **No face in multiple slots** — each `(tetra_id, face)` pair appears at most once across
   all adjacency sides and boundary faces.
7. **Every non-boundary face matched exactly once** — no unaccounted-for internal face.
8. **Adjacency vertex-set consistency** — both sides of each adjacency record name the same
   3 vertices.
9. **Orientation consistency** *(only if `oriented` in `declared_invariants`)* — shared faces
   have opposite cyclic vertex order.
10. **Boundary accounting complete** — if `closed_boundary` declared, every boundary edge
    appears in exactly 2 boundary faces.
11. **Connectivity** *(only if `connected` in `declared_invariants`)*.
12. **Canonical hash reproduction** — if `topology_hash` is present, recompute and compare.

---

## 7. Receipt Format

```json
{
  "protocol": "TMP-v1",
  "mesh_id": "<mesh_id>",
  "vertex_count": 4,
  "tetra_count": 1,
  "adjacency_count": 0,
  "boundary_face_count": 4,
  "canonical_sha256": "sha256:<64 lowercase hex chars>",
  "verdict": "PASS"
}
```

The receipt is always emitted, even on `FAIL` or `ERROR`. Fields that cannot be computed are
set to `null`.

---

## 8. Versioning and Certification

- This document specifies **TMP v1** with `canonicalization_version = "c14n-v1"`.
- Once certified (see `docs/TMP_CERTIFICATION_RULES.md`), the verifier semantics and
  canonicalization rules MUST NOT change.
- New versions use a different `protocol` string (e.g., `"TMP-v2"`).

See also:
- [`schemas/tmp_mesh.schema.json`](schemas/tmp_mesh.schema.json) — JSON schema
- [`docs/CANONICALIZATION.md`](docs/CANONICALIZATION.md) — canonicalization rules
- [`verifier/verify_tmp_mesh.py`](verifier/verify_tmp_mesh.py) — reference verifier