#!/usr/bin/env python3
"""
TMP v1 Reference Verifier

Usage:
    python verifier/verify_tmp_mesh.py <mesh.json>

Exit codes:
    0 = PASS  — all checks pass; canonical hash matches declared value
    1 = FAIL  — structural or topological validation failure
    2 = ERROR — runtime error (file not found, JSON parse failure, non-object input)

Verifier checks (ordered):
    1.  Schema validity — required fields present, protocol/version/c14n constants correct
    2.  Distinct vertex references per tetra
    3.  No duplicate tetrahedra after normalization
    4.  Face enumeration correctness (each tetra has exactly 4 distinct vertices)
    5.  Adjacency references valid tetra/face pairs
    6.  No face slot appears in more than one adjacency or boundary record
    7.  Every non-boundary face matched exactly once in adjacency
    8.  Orientation consistency across shared faces
    9.  Boundary accounting complete (no interior face declared as boundary)
    10. Canonical hash reproduction
    11. Declared invariant counts match actual mesh dimensions
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple


PROTOCOL = "TMP-v1"
VERSION = "1.0"
CANON_VERSION = "tmp-c14n-v1"

REQUIRED_TOP_LEVEL = [
    "protocol",
    "version",
    "mesh_id",
    "vertex_ids",
    "tetrahedra",
    "adjacency",
    "boundary_faces",
    "orientation_rule",
    "canonicalization_version",
    "declared_invariants",
]


# ---------------------------------------------------------------------------
# Canonicalization helpers
# ---------------------------------------------------------------------------

def canonical_json_bytes(obj: Any) -> bytes:
    """Canonical JSON: sorted keys, no insignificant whitespace, UTF-8."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def face_vertex_set(tetra_vertices: List[str], face_idx: int) -> Tuple[str, ...]:
    """
    Returns the sorted vertex triple for face `face_idx` of a tetrahedron.
    Face i is opposite to vertex index i (i.e., all vertices except the i-th).
    """
    return tuple(sorted(v for j, v in enumerate(tetra_vertices) if j != face_idx))


def face_ordered_vertices(tetra_vertices: List[str], face_idx: int) -> Tuple[str, ...]:
    """Face vertices in tetra-local order (excluding vertex at face_idx position)."""
    return tuple(v for j, v in enumerate(tetra_vertices) if j != face_idx)


def is_reverse_cyclic(a: Tuple[str, ...], b: Tuple[str, ...]) -> bool:
    """Return True if b is a reverse cyclic permutation of a."""
    n = len(a)
    a_rev = a[::-1]
    for shift in range(n):
        if tuple(a_rev[(i + shift) % n] for i in range(n)) == b:
            return True
    return False


def compute_canonical_topology(mesh: Dict[str, Any]) -> bytes:
    """
    Compute canonical topology projection bytes for SHA-256 hashing.

    Canonicalization rules (tmp-c14n-v1):
      - Sort vertex_ids lexicographically.
      - Normalize each tetra: sort vertex IDs; sort tetra records by
        (sorted_vertices, tetra_id).
      - Normalize adjacency pairs: ensure left <= right by (tetra_id, face);
        sort adjacency list lexicographically.
      - Sort boundary_faces by (tetra_id, face).
      - Include: mesh_id, canonicalization_version, orientation_rule,
        vertex_ids, tetrahedra, adjacency, boundary_faces.
      - Exclude: protocol, version, declared_invariants, geometry.
      - Serialize as compact JSON with sorted keys, UTF-8.
    """
    vertex_ids = sorted(mesh["vertex_ids"])

    def norm_tetra(t: Dict[str, Any]) -> Dict[str, Any]:
        return {"tetra_id": t["tetra_id"], "vertices": sorted(t["vertices"])}

    tetras = sorted(
        [norm_tetra(t) for t in mesh["tetrahedra"]],
        key=lambda t: (t["vertices"], t["tetra_id"]),
    )

    def norm_adj(a: Dict[str, Any]) -> Dict[str, Any]:
        left = (a["left"]["tetra_id"], a["left"]["face"])
        right = (a["right"]["tetra_id"], a["right"]["face"])
        if left > right:
            left, right = right, left
        return {
            "left":  {"face": left[1],  "tetra_id": left[0]},
            "right": {"face": right[1], "tetra_id": right[0]},
        }

    adj = sorted(
        [norm_adj(a) for a in mesh["adjacency"]],
        key=lambda a: (
            a["left"]["tetra_id"], a["left"]["face"],
            a["right"]["tetra_id"], a["right"]["face"],
        ),
    )

    boundary = sorted(
        [{"face": b["face"], "tetra_id": b["tetra_id"]} for b in mesh["boundary_faces"]],
        key=lambda b: (b["tetra_id"], b["face"]),
    )

    projection = {
        "adjacency": adj,
        "boundary_faces": boundary,
        "canonicalization_version": mesh["canonicalization_version"],
        "mesh_id": mesh["mesh_id"],
        "orientation_rule": mesh["orientation_rule"],
        "tetrahedra": tetras,
        "vertex_ids": vertex_ids,
    }
    return canonical_json_bytes(projection)


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------

def verify_tmp_mesh(mesh: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Run all TMP v1 verifier checks in order.

    Returns (verdict, errors) where verdict is 'PASS', 'FAIL', or 'ERROR',
    and errors is a list of human-readable error messages.
    """
    errors: List[str] = []

    # ------------------------------------------------------------------
    # Check 1: Schema validity
    # ------------------------------------------------------------------
    for field in REQUIRED_TOP_LEVEL:
        if field not in mesh:
            errors.append(f"check_1_schema: missing required field '{field}'")
    if mesh.get("protocol") != PROTOCOL:
        errors.append(
            f"check_1_schema: protocol must be '{PROTOCOL}', "
            f"got '{mesh.get('protocol')}'"
        )
    if mesh.get("version") != VERSION:
        errors.append(
            f"check_1_schema: version must be '{VERSION}', "
            f"got '{mesh.get('version')}'"
        )
    if mesh.get("canonicalization_version") != CANON_VERSION:
        errors.append(
            f"check_1_schema: canonicalization_version must be '{CANON_VERSION}', "
            f"got '{mesh.get('canonicalization_version')}'"
        )
    if errors:
        return "FAIL", errors

    vertex_ids: List[str] = mesh["vertex_ids"]
    tetrahedra: List[Dict[str, Any]] = mesh["tetrahedra"]
    adjacency: List[Dict[str, Any]] = mesh["adjacency"]
    boundary_faces: List[Dict[str, Any]] = mesh["boundary_faces"]
    vertex_id_set = set(vertex_ids)

    tetra_by_id: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Check 2: Distinct vertex references per tetra
    # ------------------------------------------------------------------
    for tetra in tetrahedra:
        tid = tetra.get("tetra_id", "<unknown>")
        verts = tetra.get("vertices", [])
        if len(set(verts)) != 4:
            errors.append(
                f"check_2_distinct_vertices: tetra '{tid}' has non-distinct "
                f"vertices: {verts}"
            )
        for v in verts:
            if v not in vertex_id_set:
                errors.append(
                    f"check_2_distinct_vertices: tetra '{tid}' references "
                    f"undeclared vertex '{v}'"
                )
        tetra_by_id[tid] = verts

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 3: No duplicate tetrahedra after normalization
    # ------------------------------------------------------------------
    seen_tetras: Dict[Tuple[str, ...], str] = {}
    for t in tetrahedra:
        norm = tuple(sorted(t["vertices"]))
        if norm in seen_tetras:
            errors.append(
                f"check_3_no_duplicates: tetra '{t['tetra_id']}' is a duplicate "
                f"of '{seen_tetras[norm]}' (normalized vertices: {list(norm)})"
            )
        else:
            seen_tetras[norm] = t["tetra_id"]

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 4: Face enumeration correctness
    # ------------------------------------------------------------------
    for tetra in tetrahedra:
        if len(tetra["vertices"]) != 4:
            errors.append(
                f"check_4_face_enum: tetra '{tetra['tetra_id']}' must have "
                f"exactly 4 vertices, got {len(tetra['vertices'])}"
            )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 5: Adjacency references valid tetra/face pairs
    # ------------------------------------------------------------------
    for i, adj in enumerate(adjacency):
        for side, ref in [("left", adj.get("left", {})), ("right", adj.get("right", {}))]:
            tid = ref.get("tetra_id")
            face = ref.get("face")
            if tid not in tetra_by_id:
                errors.append(
                    f"check_5_adj_valid: adjacency[{i}].{side} references "
                    f"undeclared tetra '{tid}'"
                )
            elif face not in range(4):
                errors.append(
                    f"check_5_adj_valid: adjacency[{i}].{side} face index "
                    f"{face} out of range [0, 3]"
                )

    for i, bf in enumerate(boundary_faces):
        tid = bf.get("tetra_id")
        face = bf.get("face")
        if tid not in tetra_by_id:
            errors.append(
                f"check_5_adj_valid: boundary_faces[{i}] references "
                f"undeclared tetra '{tid}'"
            )
        elif face not in range(4):
            errors.append(
                f"check_5_adj_valid: boundary_faces[{i}] face index "
                f"{face} out of range [0, 3]"
            )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 6: No face slot appears in more than one adjacency or boundary record
    # ------------------------------------------------------------------
    slot_usage: Dict[Tuple[str, int], str] = {}

    def claim_slot(tetra_id: str, face: int, record_label: str) -> None:
        key = (tetra_id, face)
        if key in slot_usage:
            errors.append(
                f"check_6_no_duplicate_slots: face ({tetra_id}, face={face}) "
                f"appears in both '{slot_usage[key]}' and '{record_label}'"
            )
        else:
            slot_usage[key] = record_label

    for i, adj in enumerate(adjacency):
        claim_slot(adj["left"]["tetra_id"],  adj["left"]["face"],  f"adjacency[{i}].left")
        claim_slot(adj["right"]["tetra_id"], adj["right"]["face"], f"adjacency[{i}].right")

    for i, bf in enumerate(boundary_faces):
        claim_slot(bf["tetra_id"], bf["face"], f"boundary_faces[{i}]")

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 7: Every non-boundary face matched exactly once
    # ------------------------------------------------------------------
    # Compute face vertex-sets for all tetra faces.
    # face_vertex_map: sorted_vertex_triple -> list of (tetra_id, face_idx)
    face_vertex_map: Dict[Tuple[str, ...], List[Tuple[str, int]]] = {}
    for tetra in tetrahedra:
        tid = tetra["tetra_id"]
        verts = tetra["vertices"]
        for face_idx in range(4):
            vset = face_vertex_set(verts, face_idx)
            face_vertex_map.setdefault(vset, []).append((tid, face_idx))

    adj_slots = set()
    for adj in adjacency:
        adj_slots.add((adj["left"]["tetra_id"],  adj["left"]["face"]))
        adj_slots.add((adj["right"]["tetra_id"], adj["right"]["face"]))

    boundary_slots = {(bf["tetra_id"], bf["face"]) for bf in boundary_faces}

    for vset, faces in face_vertex_map.items():
        if len(faces) == 1:
            tid, fidx = faces[0]
            if (tid, fidx) not in boundary_slots:
                errors.append(
                    f"check_7_face_coverage: face {list(vset)} of tetra '{tid}' "
                    f"(face {fidx}) is a boundary face but not declared in boundary_faces"
                )
        elif len(faces) == 2:
            tid0, f0 = faces[0]
            tid1, f1 = faces[1]
            pair_in_adj = any(
                (
                    (a["left"]["tetra_id"] == tid0 and a["left"]["face"] == f0 and
                     a["right"]["tetra_id"] == tid1 and a["right"]["face"] == f1)
                    or
                    (a["left"]["tetra_id"] == tid1 and a["left"]["face"] == f1 and
                     a["right"]["tetra_id"] == tid0 and a["right"]["face"] == f0)
                )
                for a in adjacency
            )
            if not pair_in_adj:
                errors.append(
                    f"check_7_face_coverage: interior face {list(vset)} shared by "
                    f"'{tid0}' (face {f0}) and '{tid1}' (face {f1}) is not in adjacency"
                )
            if (tid0, f0) in boundary_slots:
                errors.append(
                    f"check_7_face_coverage: interior face {list(vset)} of tetra "
                    f"'{tid0}' (face {f0}) is incorrectly declared as a boundary face"
                )
            if (tid1, f1) in boundary_slots:
                errors.append(
                    f"check_7_face_coverage: interior face {list(vset)} of tetra "
                    f"'{tid1}' (face {f1}) is incorrectly declared as a boundary face"
                )
        else:
            errors.append(
                f"check_7_face_coverage: face {list(vset)} appears in "
                f"{len(faces)} tetra faces (maximum allowed: 2)"
            )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 8: Orientation consistency across shared faces
    # ------------------------------------------------------------------
    for adj in adjacency:
        lt = adj["left"]["tetra_id"]
        lf = adj["left"]["face"]
        rt = adj["right"]["tetra_id"]
        rf = adj["right"]["face"]

        left_verts  = face_ordered_vertices(tetra_by_id[lt], lf)
        right_verts = face_ordered_vertices(tetra_by_id[rt], rf)

        if not is_reverse_cyclic(left_verts, right_verts):
            errors.append(
                f"check_8_orientation: shared face between '{lt}' (face {lf}) "
                f"and '{rt}' (face {rf}) has inconsistent orientation "
                f"(left={list(left_verts)}, right={list(right_verts)})"
            )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 9: Boundary accounting complete
    # ------------------------------------------------------------------
    for i, bf in enumerate(boundary_faces):
        tid  = bf["tetra_id"]
        fidx = bf["face"]
        vset = face_vertex_set(tetra_by_id[tid], fidx)
        occurrence_count = len(face_vertex_map.get(vset, []))
        if occurrence_count != 1:
            errors.append(
                f"check_9_boundary: boundary_faces[{i}] ({tid}, face={fidx}) "
                f"has vertex set {list(vset)} shared by {occurrence_count} "
                f"tetra faces (expected 1 for a boundary face)"
            )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 10: Canonical hash reproduction
    # ------------------------------------------------------------------
    canonical_bytes = compute_canonical_topology(mesh)
    computed_hash = sha256_hex(canonical_bytes)

    declared_invariants = mesh.get("declared_invariants", {})
    declared_hash: Optional[str] = declared_invariants.get("canonical_sha256")

    if declared_hash is None:
        errors.append("check_10_hash: declared_invariants.canonical_sha256 is missing")
    elif declared_hash != computed_hash:
        errors.append(
            f"check_10_hash: canonical_sha256 mismatch — "
            f"declared='{declared_hash}', computed='{computed_hash}'"
        )

    if errors:
        return "FAIL", errors

    # ------------------------------------------------------------------
    # Check 11: Declared invariant counts
    # ------------------------------------------------------------------
    count_checks = [
        ("vertex_count",        len(vertex_ids)),
        ("tetra_count",         len(tetrahedra)),
        ("adjacency_count",     len(adjacency)),
        ("boundary_face_count", len(boundary_faces)),
    ]
    for key, actual in count_checks:
        if key in declared_invariants:
            expected = declared_invariants[key]
            if expected != actual:
                errors.append(
                    f"check_11_invariants: {key} mismatch — "
                    f"declared={expected}, actual={actual}"
                )

    if errors:
        return "FAIL", errors

    return "PASS", []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="TMP v1 Reference Verifier — validates mesh topology fail-closed."
    )
    parser.add_argument("mesh_file", help="Path to TMP mesh JSON file")
    args = parser.parse_args()

    # Load and parse
    try:
        with open(args.mesh_file, "r", encoding="utf-8") as fh:
            mesh = json.load(fh)
    except OSError as exc:
        print(f"ERROR: Cannot open '{args.mesh_file}': {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON parse error in '{args.mesh_file}': {exc}", file=sys.stderr)
        return 2

    if not isinstance(mesh, dict):
        print(
            f"ERROR: '{args.mesh_file}' must be a JSON object, "
            f"got {type(mesh).__name__}",
            file=sys.stderr,
        )
        return 2

    verdict, errors = verify_tmp_mesh(mesh)

    # Compute canonical hash for receipt (best-effort)
    canonical_hash: Optional[str] = None
    try:
        canonical_hash = sha256_hex(compute_canonical_topology(mesh))
    except Exception:
        pass

    receipt: Dict[str, Any] = {
        "protocol":            "TMP-v1",
        "mesh_id":             mesh.get("mesh_id", "unknown"),
        "vertex_count":        len(mesh.get("vertex_ids", [])),
        "tetra_count":         len(mesh.get("tetrahedra", [])),
        "adjacency_count":     len(mesh.get("adjacency", [])),
        "boundary_face_count": len(mesh.get("boundary_faces", [])),
        "canonical_sha256":    canonical_hash,
        "verdict":             verdict,
    }
    if errors:
        receipt["errors"] = errors

    print(json.dumps(receipt, indent=2))

    if verdict == "PASS":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
