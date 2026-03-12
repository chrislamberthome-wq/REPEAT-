"""
verifier/verify_mesh.py

Runs full mesh verification against all TMP protocol invariants,
then generates a REPEAT-compatible receipt.

Verification steps:
  1.  Canonicalise the mesh state.
  2.  For each cell, call verify_cell (invariants 3.1 – 3.5).
  3.  Check adjacency consistency across the whole mesh (invariant 3.5).
  4.  Compute SHA-256 of the canonical JSON.
  5.  Emit a receipt conforming to tetra_mesh_receipt.schema.json.
"""

import hashlib
import json
from datetime import datetime, timezone

from .canonicalize_mesh import canonicalize_mesh
from .verify_cell import verify_cell

VERIFIER_VERSION = "tmp_v1"


def _check_adjacency(cells):
    """
    Verify that shared faces between neighbouring cells use identical
    vertex triples (invariant 3.5 – adjacency consistency).

    A face is represented as a frozenset of three vertex IDs; any face
    appearing in more than one cell must reference *exactly* the same
    three vertex IDs in both cells (i.e. canonical sorted triple matches).

    Returns
    -------
    list[str]
        List of failure descriptions; empty if adjacency is consistent.
    """
    failures = []
    # Map canonical face → list of (cell_id, raw_face_triple)
    face_registry = {}
    for cell in cells:
        cell_id = cell.get("cell_id", "<unknown>")
        for face in cell.get("faces", []):
            key = frozenset(face)
            canonical_triple = sorted(face)
            if key not in face_registry:
                face_registry[key] = (cell_id, canonical_triple)
            else:
                prev_cell_id, prev_triple = face_registry[key]
                if sorted(face) != prev_triple:
                    failures.append(
                        f"adjacency conflict on face {sorted(face)!r} "
                        f"between cell '{prev_cell_id}' and cell '{cell_id}'"
                    )
    return failures


def verify_mesh(mesh_state, prev_receipt_hash=None):
    """
    Verify a tetrahedral mesh state and return a receipt dict.

    Parameters
    ----------
    mesh_state : dict
        Raw mesh state conforming to ``tetra_mesh_state.schema.json``.
    prev_receipt_hash : str or None
        SHA-256 hex digest of the previous receipt in the chain, for
        chaining / replay verification.  Pass ``None`` for the first
        receipt.

    Returns
    -------
    dict
        A receipt conforming to ``tetra_mesh_receipt.schema.json``.
        ``result`` is ``"PASS"``, ``"FAIL"``, or ``"ERROR"``.
    """
    all_failures = []

    try:
        canonical = canonicalize_mesh(mesh_state)
        mesh_id = canonical["mesh_id"]
        cells = canonical["cells"]
        cell_count = len(cells)

        # Per-cell invariants
        for cell in cells:
            passed, cell_failures = verify_cell(cell)
            all_failures.extend(cell_failures)

        # Adjacency consistency across the mesh
        adj_failures = _check_adjacency(cells)
        all_failures.extend(adj_failures)

        # Canonical hash – serialise the already-canonicalized object to
        # avoid redundant work and ensure consistency.
        c_json = json.dumps(canonical, sort_keys=True,
                            separators=(",", ":"), ensure_ascii=False)
        canonical_hash = hashlib.sha256(c_json.encode("utf-8")).hexdigest()

        result = "PASS" if not all_failures else "FAIL"

    except Exception as exc:  # noqa: BLE001
        mesh_id = mesh_state.get("mesh_id", "<unknown>") if isinstance(mesh_state, dict) else "<unknown>"
        cell_count = 0
        canonical_hash = "0" * 64
        all_failures = [f"ERROR during processing: {exc}"]
        result = "ERROR"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    receipt = {
        "receipt_type": "tetra_mesh_verification",
        "mesh_id": mesh_id,
        "cell_count": cell_count,
        "timestamp": timestamp,
        "canonical_hash": canonical_hash,
        "prev_receipt_hash": prev_receipt_hash,
        "verifier_version": VERIFIER_VERSION,
        "result": result,
    }
    if all_failures:
        receipt["failures"] = all_failures

    return receipt
