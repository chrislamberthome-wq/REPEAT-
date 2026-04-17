# TMP v1 Canonicalization Rules (c14n-v1)

## 1. Purpose

This document defines the canonical serialization and hashing procedure for TMP v1 mesh
objects (`canonicalization_version = "c14n-v1"`). A canonical form is a unique byte sequence
for a topological object, enabling deterministic identity across implementations, languages,
and platforms.

The canonical hash allows any verifier to independently reproduce the `topology_hash` of a
TMP v1 mesh and confirm it has not been altered.

---

## 2. Encoding

- All text is **UTF-8**, no BOM.
- The canonical form is a JSON object with **no insignificant whitespace**: no spaces after
  `:` or `,`, no newlines, no indentation.
- Numbers use shortest JSON form preserving value. No `NaN`, `Infinity`, leading `+`, or
  leading zeros (except `0` itself).
- Strings use strict JSON escaping (RFC 8259).
- Duplicate keys are **illegal**; the verifier MUST return `ERROR` if any are detected.

---

## 3. Object Key Sort Order

All JSON object keys at every level are sorted **lexicographically by Unicode codepoint**
(ascending). This applies recursively to nested objects.

Example:
```json
{"adjacency":[],"boundary_faces":[...],"canonicalization_version":"c14n-v1",...}
```

---

## 4. Array Normalization Order

Top-level arrays in the canonical form are sorted as follows before serialization:

| Array field | Sort key |
|-------------|----------|
| `vertex_ids` | Lexicographic string order |
| `tetrahedra` | Normalized vertex list (see §5), then `tetra_id` |
| `adjacency` | `(left.tetra_id, left.face, right.tetra_id, right.face)` after pair normalization (§6) |
| `boundary_faces` | `(tetra_id, face)` |
| `declared_invariants` | Lexicographic string order |

---

## 5. Tetrahedron Orientation Normalization

For a tetrahedron with vertex list `[v_a, v_b, v_c, v_d]`, the canonical form uses the
**lexicographically smallest even permutation** of the vertex list.

An even permutation preserves the orientation (handedness) of the tetrahedron. There are
exactly 12 even permutations of 4 elements.

**Procedure:**
1. Generate all 12 even permutations of the vertex index tuple `(0, 1, 2, 3)`.
2. Apply each permutation to the vertex list to obtain 12 candidate lists.
3. Select the lexicographically smallest candidate list.
4. Replace the tetrahedron's `vertices` with the normalized list before hashing.

A permutation `p` is even if and only if the number of inversions (pairs `i < j` where
`p[i] > p[j]`) is even.

---

## 6. Adjacency Pair Normalization

For each `AdjacencyRecord`, the `left` and `right` sides are ordered canonically:

1. Compute `left_key = (left.tetra_id, left.face)`.
2. Compute `right_key = (right.tetra_id, right.face)`.
3. If `right_key < left_key` (lexicographic comparison), swap `left` and `right`.
4. Result: `left_key <= right_key` always.

This ensures that the same logical adjacency is always serialized the same way regardless
of how it was authored.

---

## 7. Topology-Only Projection

The canonical hash is computed over a **topology-only projection** that includes:

```
protocol
version
mesh_id
vertex_ids
tetrahedra
adjacency
boundary_faces
orientation_rule
canonicalization_version
declared_invariants
```

The following fields are **excluded** from the topology projection:
- `geometry` — optional coordinate metadata
- `topology_hash` — the hash field itself

If a separate `geometry_hash` is desired, it is computed independently from the `geometry`
block alone using the same canonical JSON + SHA-256 procedure.

---

## 8. Hash Generation Algorithm

```
procedure compute_topology_hash(mesh):
  1. Deep-copy the mesh object.
  2. Normalize vertex_ids: sort lexicographically.
  3. Normalize each tetrahedron: replace vertices with the lexicographically
     smallest even permutation (§5).
  4. Sort tetrahedra by (normalized_vertices, tetra_id).
  5. Normalize each adjacency pair: apply §6 ordering.
  6. Sort adjacency list by (left.tetra_id, left.face, right.tetra_id, right.face).
  7. Sort boundary_faces by (tetra_id, face).
  8. Sort declared_invariants lexicographically.
  9. Extract topology projection (§7): drop geometry and topology_hash fields.
  10. Serialize to canonical JSON (§2–3): UTF-8, sorted keys, no whitespace.
  11. Compute SHA-256 over the canonical byte string.
  12. Return "sha256:" + lowercase_hex(digest).
```

---

## 9. Canonical JSON Serialization Rules

The canonical JSON encoder MUST:

1. Encode as UTF-8 bytes (no BOM).
2. Sort all object keys lexicographically by Unicode codepoint.
3. Emit no insignificant whitespace.
4. Use shortest-form numbers (e.g., `1` not `1.0`, `0.5` not `5e-1`).
5. Escape only characters required by RFC 8259.
6. Arrays preserve their already-normalized order.

---

## 10. Reference Hash Vectors

The following test vectors are defined in `tests/golden/`:

| File | Expected Verdict | Topology Hash |
|------|-----------------|---------------|
| `pass_minimal_tet.json` | PASS | see file `topology_hash` field |
| `pass_cube_5tet.json` | PASS | see file `topology_hash` field |
| `fail_duplicate_tet.json` | FAIL | (not checked) |
| `fail_broken_adjacency.json` | FAIL | (not checked) |
| `fail_boundary_mismatch.json` | FAIL | (not checked) |
| `error_malformed_schema.json` | ERROR | (not checked) |

These vectors are frozen once TMP v1 is certified. See `docs/TMP_CERTIFICATION_RULES.md`.
