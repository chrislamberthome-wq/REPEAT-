"""
Tetrahedral Mesh Verifier — REPEAT TMP v1.

Implements canonicalization, invariant checks, and receipt emission for
tetrahedral mesh state per TETRAHEDRAL_MESH_PROTOCOL_v1.

Exit codes (when used via CLI):
    0 = PASS
    1 = FAIL (invariant violation)
    2 = ERROR (malformed input)
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

VERIFIER_VERSION = "tmp_v1"
SHA256_PREFIX = "sha256:"
VOLUME_TOLERANCE = 1e-9


# ---------------------------------------------------------------------------
# Canonical JSON helpers (REPEAT C14N v1 — JCS / RFC 8785)
# ---------------------------------------------------------------------------

def canonical_json(obj: Any) -> bytes:
    """Return deterministic UTF-8 JSON bytes (keys sorted, no whitespace)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def sha256_c14n(obj: Any) -> str:
    """Compute sha256 of canonical JSON and return 'sha256:<hex>' string."""
    return SHA256_PREFIX + hashlib.sha256(canonical_json(obj)).hexdigest()


# ---------------------------------------------------------------------------
# Volume computation
# ---------------------------------------------------------------------------

def compute_signed_volume(
    v1: Tuple[float, float, float],
    v2: Tuple[float, float, float],
    v3: Tuple[float, float, float],
    v4: Tuple[float, float, float],
) -> float:
    """
    Compute signed volume of a tetrahedron defined by four vertices.

    V = det(v2-v1, v3-v1, v4-v1) / 6
    """
    a = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
    b = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
    c = (v4[0] - v1[0], v4[1] - v1[1], v4[2] - v1[2])
    det = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
    return det / 6.0


# ---------------------------------------------------------------------------
# Cell canonicalization
# ---------------------------------------------------------------------------

def canonicalize_cell(cell: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a canonical representation of a tetrahedral cell.

    Rules applied:
    - vertex_ids sorted lexicographically
    - edges derived as sorted pairs, then sorted
    - faces derived as sorted triples, then sorted
    - vertex coordinate lists rounded to 9 decimal places
    - JSON keys will be sorted by canonical_json
    """
    vertex_ids = sorted(cell["vertex_ids"])
    raw_vertices: Dict[str, List[float]] = cell["vertices"]

    # Round coordinates for cross-platform consistency (fixed decimal precision)
    vertices: Dict[str, List[float]] = {
        vid: [round(c, 9) for c in raw_vertices[vid]]
        for vid in vertex_ids
    }

    # Derive edges (all pairs, each pair sorted, set sorted)
    edges: List[List[str]] = sorted(
        [sorted([vertex_ids[i], vertex_ids[j]])
         for i in range(4) for j in range(i + 1, 4)]
    )

    # Derive faces (all triples, each triple sorted, set sorted)
    faces: List[List[str]] = sorted(
        [sorted([vertex_ids[i], vertex_ids[j], vertex_ids[k]])
         for i in range(4) for j in range(i + 1, 4) for k in range(j + 1, 4)]
    )

    coords = [tuple(vertices[vid]) for vid in vertex_ids]
    volume = compute_signed_volume(*coords)
    orientation = "positive" if volume > 0 else "negative"

    return {
        "cell_id": cell["cell_id"],
        "edges": edges,
        "faces": faces,
        "orientation": orientation,
        "vertex_ids": vertex_ids,
        "vertices": vertices,
        "volume": round(volume, 9),
    }


# ---------------------------------------------------------------------------
# Cell invariant checks
# ---------------------------------------------------------------------------

def verify_cell(cell: Dict[str, Any]) -> List[str]:
    """
    Check all invariants for a single tetrahedral cell.

    Returns a list of error strings (empty list = PASS).
    """
    errors: List[str] = []
    cid = cell.get("cell_id", "<unknown>")

    # 3.1 Structural validity
    vids = cell.get("vertex_ids", [])
    if len(vids) != 4:
        errors.append(f"cell {cid}: expected 4 vertex_ids, got {len(vids)}")
        return errors  # Can't proceed without 4 vertices

    vertices = cell.get("vertices", {})
    for vid in vids:
        if vid not in vertices:
            errors.append(f"cell {cid}: vertex_id '{vid}' missing from vertices map")
            return errors

    # 3.4 Signed volume (non-degenerate check)
    coords = [tuple(vertices[vid]) for vid in vids]
    try:
        volume = compute_signed_volume(*coords)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"cell {cid}: volume computation error: {exc}")
        return errors

    if abs(volume) <= VOLUME_TOLERANCE:
        errors.append(
            f"cell {cid}: degenerate tetrahedron (|volume|={abs(volume):.2e} "
            f"<= tolerance {VOLUME_TOLERANCE:.2e})"
        )

    # 3.2 Edge consistency — derived from vertex_ids must match stored edges
    canonical = canonicalize_cell(cell)
    stored_edges = [sorted(e) for e in cell.get("edges", [])]
    if stored_edges and sorted(stored_edges) != sorted(canonical["edges"]):
        errors.append(f"cell {cid}: edge list inconsistent with vertex_ids")

    stored_faces = [sorted(f) for f in cell.get("faces", [])]
    if stored_faces and sorted(stored_faces) != sorted(canonical["faces"]):
        errors.append(f"cell {cid}: face list inconsistent with vertex_ids")

    # 3.3 Orientation consistency
    stored_orientation = cell.get("orientation")
    if stored_orientation and stored_orientation != canonical["orientation"]:
        errors.append(
            f"cell {cid}: orientation mismatch: stored='{stored_orientation}', "
            f"computed='{canonical['orientation']}'"
        )

    return errors


# ---------------------------------------------------------------------------
# Mesh verification
# ---------------------------------------------------------------------------

def verify_mesh(mesh: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify a tetrahedral mesh and return a TMP receipt.

    The receipt contains 'result': 'PASS', 'FAIL', or 'ERROR'.
    """
    mesh_id = mesh.get("mesh_id", "<unknown>")
    cells = mesh.get("cells", [])

    if not isinstance(cells, list):
        return _error_receipt(mesh_id, 0, "cells field is not a list")

    all_errors: List[str] = []
    canonical_cells = []

    for cell in cells:
        if not isinstance(cell, dict):
            all_errors.append(f"mesh {mesh_id}: cell is not an object")
            continue
        cell_errors = verify_cell(cell)
        all_errors.extend(cell_errors)
        if not cell_errors:
            canonical_cells.append(canonicalize_cell(cell))

    # Build canonical mesh state for hashing (exclude derived/receipt fields)
    canonical_state = {
        "cells": sorted(canonical_cells, key=lambda c: c["cell_id"]),
        "mesh_id": mesh_id,
    }
    canonical_hash = sha256_c14n(canonical_state)

    result = "PASS" if not all_errors else "FAIL"

    receipt: Dict[str, Any] = {
        "canonical_hash": canonical_hash,
        "cell_count": len(cells),
        "errors": all_errors,
        "mesh_id": mesh_id,
        "receipt_type": "tetra_mesh_verification",
        "result": result,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verifier_version": VERIFIER_VERSION,
    }
    return receipt


def _error_receipt(mesh_id: str, cell_count: int, message: str) -> Dict[str, Any]:
    return {
        "canonical_hash": "",
        "cell_count": cell_count,
        "errors": [message],
        "mesh_id": mesh_id,
        "receipt_type": "tetra_mesh_verification",
        "result": "ERROR",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verifier_version": VERIFIER_VERSION,
    }


# ---------------------------------------------------------------------------
# Mesh hash — stable across invocations (no timestamp)
# ---------------------------------------------------------------------------

def compute_mesh_hash(mesh: Dict[str, Any]) -> str:
    """
    Compute the canonical SHA-256 hash of a tetrahedral mesh.

    This function is deterministic: it does not include any timestamp or
    run-specific data, making it suitable for golden-vector comparisons.
    """
    mesh_id = mesh.get("mesh_id", "<unknown>")
    cells = mesh.get("cells", [])

    canonical_cells = []
    for cell in cells:
        if isinstance(cell, dict):
            canonical_cells.append(canonicalize_cell(cell))

    canonical_state = {
        "cells": sorted(canonical_cells, key=lambda c: c["cell_id"]),
        "mesh_id": mesh_id,
    }
    return sha256_c14n(canonical_state)
