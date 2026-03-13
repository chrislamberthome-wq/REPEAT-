#!/usr/bin/env python3
"""
TMP v1 Reference Verifier
=========================

Verifies a TMP v1 mesh JSON file against schema, topological invariants,
and canonical hash.

Exit codes:
  0 — PASS:  all checks passed; canonical hash matches if declared
  1 — FAIL:  topological or structural invariant violated
  2 — ERROR: input cannot be processed (schema invalid, parse error, etc.)

Usage:
  python verify_tmp_mesh.py <mesh.json>
  python verify_tmp_mesh.py --receipt <mesh.json>   # emit receipt JSON to stdout
"""

import sys
import json
import hashlib
import argparse
import copy
import re
from itertools import permutations
from typing import Any, Dict, List, Optional, Tuple

VERIFIER_VERSION = "1.0.0"
PROTOCOL = "TMP-v1"

# Exit codes
EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2

# Valid invariant names
VALID_INVARIANTS = {"manifold_interior", "closed_boundary", "connected", "oriented"}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_json(path: str) -> Tuple[Optional[Any], Optional[str]]:
    """Load and parse a JSON file. Returns (data, error_message)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"JSON parse error: {exc}"
    except Exception as exc:  # noqa: BLE001
        return None, f"Unexpected error reading file: {exc}"


# ---------------------------------------------------------------------------
# Schema validation (check 1)
# ---------------------------------------------------------------------------

def _validate_face_ref(ref: Any, path: str, errors: List[str]) -> None:
    if not isinstance(ref, dict):
        errors.append(f"{path} must be an object")
        return
    if "tetra_id" not in ref:
        errors.append(f"{path} missing 'tetra_id'")
    elif not isinstance(ref["tetra_id"], str) or not ref["tetra_id"]:
        errors.append(f"{path}.tetra_id must be a non-empty string")
    if "face" not in ref:
        errors.append(f"{path} missing 'face'")
    elif isinstance(ref["face"], bool) or not isinstance(ref["face"], int) or \
            ref["face"] < 0 or ref["face"] > 3:
        errors.append(f"{path}.face must be an integer in 0–3")


def validate_schema(mesh: Dict) -> List[str]:
    """
    Validate the mesh object against TMP v1 schema requirements.
    Returns a list of error strings (empty list means valid).
    """
    errors: List[str] = []

    required = [
        "protocol", "version", "mesh_id", "vertex_ids", "tetrahedra",
        "adjacency", "boundary_faces", "orientation_rule",
        "canonicalization_version", "declared_invariants",
    ]
    for field in required:
        if field not in mesh:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return errors

    # protocol
    if mesh["protocol"] != PROTOCOL:
        errors.append(f"protocol must be {PROTOCOL!r}, got {mesh['protocol']!r}")

    # version: semver
    if not isinstance(mesh["version"], str) or \
            not re.match(r"^\d+\.\d+\.\d+$", mesh["version"]):
        errors.append(f"version must match x.y.z semver, got {mesh.get('version')!r}")

    # mesh_id
    if not isinstance(mesh["mesh_id"], str) or not mesh["mesh_id"]:
        errors.append("mesh_id must be a non-empty string")

    # vertex_ids
    if not isinstance(mesh["vertex_ids"], list):
        errors.append("vertex_ids must be an array")
    elif len(mesh["vertex_ids"]) < 4:
        errors.append(f"vertex_ids must have at least 4 entries, got {len(mesh['vertex_ids'])}")
    else:
        for i, v in enumerate(mesh["vertex_ids"]):
            if not isinstance(v, str) or not v:
                errors.append(f"vertex_ids[{i}] must be a non-empty string")
        if len(set(mesh["vertex_ids"])) != len(mesh["vertex_ids"]):
            errors.append("vertex_ids must be unique (duplicates detected)")

    # tetrahedra
    if not isinstance(mesh["tetrahedra"], list):
        errors.append("tetrahedra must be an array")
    elif len(mesh["tetrahedra"]) < 1:
        errors.append("tetrahedra must have at least 1 entry")
    else:
        for i, t in enumerate(mesh["tetrahedra"]):
            if not isinstance(t, dict):
                errors.append(f"tetrahedra[{i}] must be an object")
                continue
            if "tetra_id" not in t:
                errors.append(f"tetrahedra[{i}] missing 'tetra_id'")
            elif not isinstance(t["tetra_id"], str) or not t["tetra_id"]:
                errors.append(f"tetrahedra[{i}].tetra_id must be a non-empty string")
            if "vertices" not in t:
                errors.append(f"tetrahedra[{i}] missing 'vertices'")
            elif not isinstance(t["vertices"], list) or len(t["vertices"]) != 4:
                errors.append(f"tetrahedra[{i}].vertices must be an array of exactly 4 items")
            else:
                for j, v in enumerate(t["vertices"]):
                    if not isinstance(v, str) or not v:
                        errors.append(
                            f"tetrahedra[{i}].vertices[{j}] must be a non-empty string"
                        )

    # adjacency
    if not isinstance(mesh["adjacency"], list):
        errors.append("adjacency must be an array")
    else:
        for i, adj in enumerate(mesh["adjacency"]):
            if not isinstance(adj, dict):
                errors.append(f"adjacency[{i}] must be an object")
                continue
            if "left" not in adj:
                errors.append(f"adjacency[{i}] missing 'left'")
            else:
                _validate_face_ref(adj["left"], f"adjacency[{i}].left", errors)
            if "right" not in adj:
                errors.append(f"adjacency[{i}] missing 'right'")
            else:
                _validate_face_ref(adj["right"], f"adjacency[{i}].right", errors)

    # boundary_faces
    if not isinstance(mesh["boundary_faces"], list):
        errors.append("boundary_faces must be an array")
    else:
        for i, bf in enumerate(mesh["boundary_faces"]):
            if not isinstance(bf, dict):
                errors.append(f"boundary_faces[{i}] must be an object")
            else:
                _validate_face_ref(bf, f"boundary_faces[{i}]", errors)

    # orientation_rule
    if mesh.get("orientation_rule") != "right_hand_outward":
        errors.append(
            f"orientation_rule must be 'right_hand_outward', got {mesh.get('orientation_rule')!r}"
        )

    # canonicalization_version
    if mesh.get("canonicalization_version") != "c14n-v1":
        errors.append(
            f"canonicalization_version must be 'c14n-v1', "
            f"got {mesh.get('canonicalization_version')!r}"
        )

    # declared_invariants
    if not isinstance(mesh["declared_invariants"], list):
        errors.append("declared_invariants must be an array")
    else:
        for inv in mesh["declared_invariants"]:
            if inv not in VALID_INVARIANTS:
                errors.append(
                    f"declared_invariants contains unknown invariant: {inv!r}. "
                    f"Valid values: {sorted(VALID_INVARIANTS)}"
                )

    # topology_hash (optional) — validate format if present
    if "topology_hash" in mesh:
        th = mesh["topology_hash"]
        if not isinstance(th, str) or not re.match(r"^sha256:[0-9a-f]{64}$", th):
            errors.append(
                f"topology_hash must match 'sha256:<64 lowercase hex>', got {th!r}"
            )

    return errors


# ---------------------------------------------------------------------------
# Face geometry helpers
# ---------------------------------------------------------------------------

def get_face_vertices(
    tetra_vertices: List[str], face_idx: int
) -> Tuple[str, str, str]:
    """
    Return the 3 ordered vertices of a face of a tetrahedron.
    Face i is opposite to vertex at position i.
    """
    v = tetra_vertices
    face_map = {
        0: (v[1], v[2], v[3]),
        1: (v[0], v[2], v[3]),
        2: (v[0], v[1], v[3]),
        3: (v[0], v[1], v[2]),
    }
    return face_map[face_idx]


def faces_opposite_orientation(
    face_a: Tuple[str, str, str], face_b: Tuple[str, str, str]
) -> bool:
    """
    Return True if two face triples of the same 3 vertices have opposite cyclic orientation.

    Opposite orientation means face_b is a cyclic rotation of the reverse of face_a.
    If face_a = (p, q, r), then its reverse is (r, q, p), and the cyclic rotations are:
      (r, q, p), (q, p, r), (p, r, q).
    """
    p, q, r = face_a
    reversed_rotations = {(r, q, p), (q, p, r), (p, r, q)}
    return face_b in reversed_rotations


# ---------------------------------------------------------------------------
# Topological checks (checks 2–11)
# ---------------------------------------------------------------------------

def check_topology(mesh: Dict) -> Tuple[List[str], List[str]]:
    """
    Run topological checks on a schema-valid mesh.

    Returns:
        (fail_reasons, warnings)
    """
    fails: List[str] = []
    warns: List[str] = []

    vertex_set = set(mesh["vertex_ids"])
    tetra_map: Dict[str, List[str]] = {}

    # Build tetra map (unique ids validated in check 3)
    for t in mesh["tetrahedra"]:
        tetra_map[t["tetra_id"]] = t["vertices"]

    # Check 2: distinct vertex references per tetrahedron
    for t in mesh["tetrahedra"]:
        tid = t["tetra_id"]
        verts = t["vertices"]
        if len(set(verts)) != 4:
            fails.append(
                f"tetra {tid!r}: vertices are not all distinct: {verts}"
            )
        for v in verts:
            if v not in vertex_set:
                fails.append(
                    f"tetra {tid!r}: vertex {v!r} not declared in vertex_ids"
                )

    # Check 3: no duplicate tetrahedra (by sorted vertex set)
    seen_vertex_sets: Dict[tuple, str] = {}
    seen_tetra_ids: Dict[str, bool] = {}
    for t in mesh["tetrahedra"]:
        tid = t["tetra_id"]
        if tid in seen_tetra_ids:
            fails.append(f"Duplicate tetra_id: {tid!r}")
        seen_tetra_ids[tid] = True
        key = tuple(sorted(t["vertices"]))
        if key in seen_vertex_sets:
            fails.append(
                f"Duplicate tetrahedra: {tid!r} and {seen_vertex_sets[key]!r} "
                f"share the same vertex set {list(key)}"
            )
        else:
            seen_vertex_sets[key] = tid

    if fails:
        return fails, warns

    # Check 4: face accounting
    total_faces = len(mesh["tetrahedra"]) * 4
    adj_face_slots = len(mesh["adjacency"]) * 2
    boundary_count = len(mesh["boundary_faces"])
    if adj_face_slots + boundary_count != total_faces:
        fails.append(
            f"Face accounting mismatch: {len(mesh['tetrahedra'])} tetras × 4 = "
            f"{total_faces} faces, but "
            f"{len(mesh['adjacency'])} adj pairs × 2 + {boundary_count} boundary = "
            f"{adj_face_slots + boundary_count}"
        )
        return fails, warns

    # Check 5 & 6: adjacency refs valid; no face in multiple slots
    face_registry: Dict[Tuple[str, int], str] = {}

    for i, adj in enumerate(mesh["adjacency"]):
        for side in ("left", "right"):
            ref = adj[side]
            tid = ref["tetra_id"]
            fidx = ref["face"]
            if tid not in tetra_map:
                fails.append(
                    f"adjacency[{i}].{side}: unknown tetra_id {tid!r}"
                )
                continue
            key = (tid, fidx)
            if key in face_registry:
                fails.append(
                    f"adjacency[{i}].{side}: face ({tid!r}, {fidx}) already "
                    f"claimed by {face_registry[key]}"
                )
            else:
                face_registry[key] = f"adjacency[{i}].{side}"

    for i, bf in enumerate(mesh["boundary_faces"]):
        tid = bf["tetra_id"]
        fidx = bf["face"]
        if tid not in tetra_map:
            fails.append(
                f"boundary_faces[{i}]: unknown tetra_id {tid!r}"
            )
            continue
        key = (tid, fidx)
        if key in face_registry:
            fails.append(
                f"boundary_faces[{i}]: face ({tid!r}, {fidx}) already "
                f"claimed by {face_registry[key]}"
            )
        else:
            face_registry[key] = f"boundary_faces[{i}]"

    # Check 7: every (tetra, face) pair is accounted for
    for t in mesh["tetrahedra"]:
        tid = t["tetra_id"]
        for fidx in range(4):
            key = (tid, fidx)
            if key not in face_registry:
                fails.append(
                    f"Face ({tid!r}, {fidx}) is neither in adjacency nor boundary_faces"
                )

    if fails:
        return fails, warns

    # Check 8: adjacency vertex-set consistency
    for i, adj in enumerate(mesh["adjacency"]):
        lt = adj["left"]["tetra_id"]
        lf = adj["left"]["face"]
        rt = adj["right"]["tetra_id"]
        rf = adj["right"]["face"]

        left_face = get_face_vertices(tetra_map[lt], lf)
        right_face = get_face_vertices(tetra_map[rt], rf)

        if frozenset(left_face) != frozenset(right_face):
            fails.append(
                f"adjacency[{i}]: vertex-set mismatch — left face {list(left_face)} "
                f"vs right face {list(right_face)}"
            )

    if fails:
        return fails, warns

    # Check 9: orientation consistency (only if 'oriented' declared)
    orientation_issues: List[str] = []
    for i, adj in enumerate(mesh["adjacency"]):
        lt = adj["left"]["tetra_id"]
        lf = adj["left"]["face"]
        rt = adj["right"]["tetra_id"]
        rf = adj["right"]["face"]

        left_face = get_face_vertices(tetra_map[lt], lf)
        right_face = get_face_vertices(tetra_map[rt], rf)

        if not faces_opposite_orientation(left_face, right_face):
            orientation_issues.append(
                f"adjacency[{i}]: faces {list(left_face)} and {list(right_face)} "
                f"have the same cyclic orientation (expected opposite for right_hand_outward)"
            )

    if "oriented" in mesh.get("declared_invariants", []):
        fails.extend(orientation_issues)
    else:
        warns.extend(orientation_issues)

    if fails:
        return fails, warns

    # Check 10: closed_boundary invariant
    if "closed_boundary" in mesh.get("declared_invariants", []):
        edge_count: Dict[tuple, int] = {}
        for bf in mesh["boundary_faces"]:
            face_verts = get_face_vertices(tetra_map[bf["tetra_id"]], bf["face"])
            for j in range(3):
                edge = tuple(sorted([face_verts[j], face_verts[(j + 1) % 3]]))
                edge_count[edge] = edge_count.get(edge, 0) + 1
        bad_edges = [e for e, cnt in edge_count.items() if cnt != 2]
        if bad_edges:
            sample = bad_edges[:3]
            ellipsis = "..." if len(bad_edges) > 3 else ""
            fails.append(
                f"closed_boundary invariant: {len(bad_edges)} boundary edge(s) not "
                f"shared by exactly 2 boundary faces: {sample}{ellipsis}"
            )

    # Check 11: connected invariant
    if "connected" in mesh.get("declared_invariants", []):
        adj_graph: Dict[str, set] = {
            t["tetra_id"]: set() for t in mesh["tetrahedra"]
        }
        for adj in mesh["adjacency"]:
            lt = adj["left"]["tetra_id"]
            rt = adj["right"]["tetra_id"]
            adj_graph[lt].add(rt)
            adj_graph[rt].add(lt)

        start = mesh["tetrahedra"][0]["tetra_id"]
        visited: set = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                stack.extend(adj_graph[node] - visited)

        all_ids = {t["tetra_id"] for t in mesh["tetrahedra"]}
        unvisited = all_ids - visited
        if unvisited:
            sample = sorted(unvisited)[:3]
            ellipsis = "..." if len(unvisited) > 3 else ""
            fails.append(
                f"connected invariant: {len(unvisited)} tetra(s) unreachable from "
                f"{start!r}: {sample}{ellipsis}"
            )

    return fails, warns


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------

def _perm_parity(perm: Tuple[int, ...]) -> int:
    """Return 0 if permutation is even, 1 if odd (counted by inversions)."""
    inversions = 0
    for i in range(len(perm)):
        for j in range(i + 1, len(perm)):
            if perm[i] > perm[j]:
                inversions += 1
    return inversions % 2


_EVEN_PERMS_4 = [
    p for p in permutations(range(4)) if _perm_parity(p) == 0
]


def normalize_tetra_vertices(verts: List[str]) -> List[str]:
    """
    Normalize a tetrahedron's vertex list to the lexicographically smallest
    even permutation, preserving orientation.
    """
    candidates = [[verts[i] for i in p] for p in _EVEN_PERMS_4]
    return min(candidates)


def normalize_mesh_for_canonicalization(mesh: Dict) -> Dict:
    """
    Return a deep copy of the mesh with all arrays normalized for canonical serialization:

    1. Sort vertex_ids lexicographically.
    2. Normalize each tetrahedron vertex list (smallest even permutation).
    3. Sort tetrahedra by (normalized_vertices, tetra_id).
    4. Normalize adjacency pairs: left <= right (by (tetra_id, face)).
    5. Sort adjacency by (left.tetra_id, left.face, right.tetra_id, right.face).
    6. Sort boundary_faces by (tetra_id, face).
    7. Sort declared_invariants lexicographically.
    """
    m = copy.deepcopy(mesh)

    m["vertex_ids"] = sorted(m["vertex_ids"])

    for t in m["tetrahedra"]:
        t["vertices"] = normalize_tetra_vertices(t["vertices"])

    m["tetrahedra"].sort(key=lambda t: (t["vertices"], t["tetra_id"]))

    for adj in m["adjacency"]:
        left_key = (adj["left"]["tetra_id"], adj["left"]["face"])
        right_key = (adj["right"]["tetra_id"], adj["right"]["face"])
        if right_key < left_key:
            adj["left"], adj["right"] = adj["right"], adj["left"]

    m["adjacency"].sort(key=lambda a: (
        a["left"]["tetra_id"], a["left"]["face"],
        a["right"]["tetra_id"], a["right"]["face"],
    ))

    m["boundary_faces"].sort(key=lambda b: (b["tetra_id"], b["face"]))

    m["declared_invariants"] = sorted(m["declared_invariants"])

    return m


def topology_projection(mesh: Dict) -> Dict:
    """Extract the topology-only projection (excludes geometry and topology_hash)."""
    topology_fields = [
        "protocol", "version", "mesh_id", "vertex_ids", "tetrahedra",
        "adjacency", "boundary_faces", "orientation_rule",
        "canonicalization_version", "declared_invariants",
    ]
    return {k: mesh[k] for k in topology_fields if k in mesh}


def canonical_json(obj: Any) -> bytes:
    """
    Produce canonical JSON bytes:
    - UTF-8, no BOM
    - Sorted object keys (lexicographic Unicode codepoint order)
    - No insignificant whitespace
    """
    if isinstance(obj, dict):
        parts = [
            canonical_json(k) + b":" + canonical_json(v)
            for k, v in sorted(obj.items())
        ]
        return b"{" + b",".join(parts) + b"}"
    if isinstance(obj, list):
        return b"[" + b",".join(canonical_json(item) for item in obj) + b"]"
    if isinstance(obj, bool):
        return b"true" if obj else b"false"
    if obj is None:
        return b"null"
    # numbers and strings
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compute_canonical_hash(mesh: Dict) -> str:
    """
    Compute the canonical SHA-256 hash of the topology projection.
    Returns 'sha256:<64 lowercase hex chars>'.
    """
    normalized = normalize_mesh_for_canonicalization(mesh)
    projection = topology_projection(normalized)
    raw = canonical_json(projection)
    digest = hashlib.sha256(raw).hexdigest()
    return f"sha256:{digest}"


# ---------------------------------------------------------------------------
# Main verification function
# ---------------------------------------------------------------------------

def verify(mesh_path: str) -> Tuple[str, int, Dict]:
    """
    Verify a TMP v1 mesh file.

    Returns:
        (verdict, exit_code, receipt_dict)
    """
    receipt: Dict[str, Any] = {
        "protocol": PROTOCOL,
        "mesh_id": None,
        "vertex_count": None,
        "tetra_count": None,
        "adjacency_count": None,
        "boundary_face_count": None,
        "canonical_sha256": None,
        "verdict": "ERROR",
    }

    # Load JSON
    mesh, load_err = load_json(mesh_path)
    if load_err is not None:
        receipt["verdict"] = "ERROR"
        receipt["error"] = load_err
        return "ERROR", EXIT_ERROR, receipt

    if not isinstance(mesh, dict):
        receipt["verdict"] = "ERROR"
        receipt["error"] = "Top-level JSON value must be an object ({...})"
        return "ERROR", EXIT_ERROR, receipt

    # Check 1: schema validation
    schema_errors = validate_schema(mesh)
    if schema_errors:
        receipt["verdict"] = "ERROR"
        receipt["error"] = f"Schema validation failed ({len(schema_errors)} error(s))"
        receipt["schema_errors"] = schema_errors
        return "ERROR", EXIT_ERROR, receipt

    # Populate receipt metadata from validated mesh
    receipt["mesh_id"] = mesh["mesh_id"]
    receipt["vertex_count"] = len(mesh["vertex_ids"])
    receipt["tetra_count"] = len(mesh["tetrahedra"])
    receipt["adjacency_count"] = len(mesh["adjacency"])
    receipt["boundary_face_count"] = len(mesh["boundary_faces"])

    # Checks 2–11: topological invariants
    fail_reasons, _warns = check_topology(mesh)
    if fail_reasons:
        receipt["verdict"] = "FAIL"
        receipt["fail_reasons"] = fail_reasons
        return "FAIL", EXIT_FAIL, receipt

    # Check 12: canonical hash reproduction
    try:
        computed_hash = compute_canonical_hash(mesh)
    except Exception as exc:  # noqa: BLE001
        receipt["verdict"] = "ERROR"
        receipt["error"] = f"Hash computation failed: {exc}"
        return "ERROR", EXIT_ERROR, receipt

    receipt["canonical_sha256"] = computed_hash

    if "topology_hash" in mesh:
        declared = mesh["topology_hash"]
        if declared != computed_hash:
            receipt["verdict"] = "FAIL"
            receipt["fail_reasons"] = [
                f"topology_hash mismatch: declared {declared!r}, "
                f"computed {computed_hash!r}"
            ]
            return "FAIL", EXIT_FAIL, receipt

    receipt["verdict"] = "PASS"
    return "PASS", EXIT_PASS, receipt


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="TMP v1 Reference Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0 — PASS:  all checks passed
  1 — FAIL:  topological or structural invariant violated
  2 — ERROR: input cannot be processed
""",
    )
    parser.add_argument("mesh_file", help="Path to TMP v1 mesh JSON file")
    parser.add_argument(
        "--receipt",
        action="store_true",
        help="Emit the full receipt as JSON to stdout",
    )
    args = parser.parse_args()

    verdict, exit_code, receipt = verify(args.mesh_file)

    if args.receipt:
        print(json.dumps(receipt, indent=2))
    else:
        print(f"verdict: {verdict}")
        if verdict == "FAIL":
            for reason in receipt.get("fail_reasons", []):
                print(f"  FAIL: {reason}", file=sys.stderr)
        elif verdict == "ERROR":
            print(f"  ERROR: {receipt.get('error', 'unknown')}", file=sys.stderr)
            for err in receipt.get("schema_errors", []):
                print(f"    - {err}", file=sys.stderr)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
