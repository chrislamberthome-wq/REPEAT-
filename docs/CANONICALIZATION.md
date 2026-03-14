# TMP v1 Canonicalization Rules

**Document**: `docs/CANONICALIZATION.md`
**Protocol**: TMP-v1
**Canonicalization Version**: `tmp-c14n-v1`
**Status**: Normative

---

## 1. Purpose

The TMP canonicalization layer transforms a topological mesh object into a
unique, deterministic byte sequence suitable for SHA-256 hashing. Two mesh
objects with identical combinatorial topology must produce identical canonical
bytes and therefore identical digests.

Geometry (vertex coordinates) is **excluded** from the canonical topology
projection and therefore from the topology hash.

---

## 2. Inputs and Scope

The canonical projection is derived from the following top-level fields:

| Field                    | Included |
|--------------------------|----------|
| `mesh_id`                | ✓        |
| `canonicalization_version` | ✓      |
| `orientation_rule`       | ✓        |
| `vertex_ids`             | ✓        |
| `tetrahedra`             | ✓        |
| `adjacency`              | ✓        |
| `boundary_faces`         | ✓        |
| `protocol`               | ✗        |
| `version`                | ✗        |
| `declared_invariants`    | ✗        |
| `geometry`               | ✗        |

---

## 3. Normalization Steps

### 3.1 Vertex IDs

Sort `vertex_ids` lexicographically (Unicode codepoint order, UTF-8 encoded).

```
vertex_ids := sort(mesh.vertex_ids)
```

### 3.2 Tetra Records

For each tetrahedron record:

1. **Vertex normalization**: Sort the four vertex IDs within the `vertices`
   array lexicographically.
2. **Record sorting**: Sort all normalized tetra records lexicographically by
   `(sorted_vertices, tetra_id)`.

```
norm_tetra(t) := { "tetra_id": t.tetra_id, "vertices": sort(t.vertices) }
tetrahedra    := sort_by( map(norm_tetra, mesh.tetrahedra),
                          key = (t.vertices, t.tetra_id) )
```

> **Note**: Sorting within a tetra removes local vertex ordering but preserves
> the vertex set identity. Orientation consistency is checked separately by
> the verifier (check 8) and is not encoded in the topology hash.

### 3.3 Adjacency Records

For each adjacency record `{ left, right }`:

1. **Pair normalization**: Compare `(left.tetra_id, left.face)` and
   `(right.tetra_id, right.face)` lexicographically. If `left > right`, swap
   them so the canonical pair always has the lexicographically smaller side on
   the left.
2. **Record sorting**: Sort all normalized adjacency records lexicographically
   by `(left.tetra_id, left.face, right.tetra_id, right.face)`.

```
norm_adj(a) :=
  let left  = (a.left.tetra_id,  a.left.face)
      right = (a.right.tetra_id, a.right.face)
  in  if left <= right
      then { "left": to_obj(left), "right": to_obj(right) }
      else { "left": to_obj(right), "right": to_obj(left) }

adjacency := sort_by( map(norm_adj, mesh.adjacency),
                      key = (left.tetra_id, left.face,
                             right.tetra_id, right.face) )
```

### 3.4 Boundary Faces

Sort all boundary face records by `(tetra_id, face)`:

```
boundary_faces := sort_by( mesh.boundary_faces,
                            key = (b.tetra_id, b.face) )
```

---

## 4. Canonical Projection Object

Assemble the normalized fields into a single JSON-serializable object with
**sorted keys**:

```json
{
  "adjacency": [ ... ],
  "boundary_faces": [ ... ],
  "canonicalization_version": "tmp-c14n-v1",
  "mesh_id": "<value>",
  "orientation_rule": "<value>",
  "tetrahedra": [ ... ],
  "vertex_ids": [ ... ]
}
```

---

## 5. Serialization

Serialize the canonical projection object according to the following rules:

| Rule                          | Requirement                                     |
|-------------------------------|-------------------------------------------------|
| Encoding                      | UTF-8, no BOM                                   |
| Object key ordering           | Sorted (lexicographic, Unicode codepoint order) |
| Insignificant whitespace      | None (compact form)                             |
| String representation         | Unescaped where allowed (ensure_ascii=False)    |
| Numeric NaN / Infinity        | Prohibited                                      |
| Array element separator       | `,` (no space)                                  |
| Key–value separator           | `:` (no space)                                  |

This follows JCS (RFC 8785) / REPEAT C14N v1 conventions.

Reference Python serialization:

```python
import json
canonical_bytes = json.dumps(
    projection,
    ensure_ascii=False,
    sort_keys=True,
    separators=(',', ':'),
    allow_nan=False,
).encode('utf-8')
```

---

## 6. Hash Computation

```
canonical_sha256 := hex( SHA-256( canonical_bytes ) )
```

The result is a 64-character lowercase hexadecimal string with no prefix.

---

## 7. Geometry Hash (Optional)

If geometry coordinates are included and a geometry hash is desired, it MUST
be declared as a **separate field** (e.g., `geometry_sha256`) and computed
over the geometry sub-object only. The geometry hash MUST NOT be mixed with
the topology hash.

The topology hash (`canonical_sha256`) is always computed without geometry
regardless of whether a `geometry` field is present.

---

## 8. Stability Guarantee

Once a `canonical_sha256` is declared in `declared_invariants` and the mesh
passes TMP v1 certification, the following MUST NOT change without
recertification:

- Canonicalization algorithm (these rules)
- SHA-256 digest of `schemas/tmp_mesh.schema.json`
- SHA-256 digest of `verifier/verify_tmp_mesh.py`
- Golden vector canonical digests

Changes to any of the above automatically set
`TMP_CERT_DECISION=DO_NOT_CERTIFY`.
