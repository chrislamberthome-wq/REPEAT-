from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from .canonicalize_mesh import canonical_json_bytes
from .verify_cell import verify_cell
from .tmp_metadata import TMP_VERSION

VERIFIER_VERSION = TMP_VERSION


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _face_sets(cell: dict[str, Any]) -> set:
    vids = cell["vertex_ids"]
    faces = [
        tuple(sorted((vids[0], vids[1], vids[2]))),
        tuple(sorted((vids[0], vids[1], vids[3]))),
        tuple(sorted((vids[0], vids[2], vids[3]))),
        tuple(sorted((vids[1], vids[2], vids[3]))),
    ]
    return set(faces)


def verify_mesh(mesh_state: dict[str, Any]) -> dict[str, Any]:
    reasons: list = []

    for cell in mesh_state.get("cells", []):
        ok, cell_reasons = verify_cell(cell)
        if not ok:
            reasons.extend([f"{cell['cell_id']}: {r}" for r in cell_reasons])

    # Basic face-sharing sanity check:
    # a face should be shared by at most two cells.
    face_counts: dict = {}
    for cell in mesh_state.get("cells", []):
        for face in _face_sets(cell):
            face_counts[face] = face_counts.get(face, 0) + 1

    over_shared = [face for face, count in face_counts.items() if count > 2]
    for face in over_shared:
        reasons.append(f"invalid adjacency: face shared by >2 cells: {face}")

    result = "PASS" if not reasons else "FAIL"
    canonical_hash = sha256_hex(canonical_json_bytes(mesh_state))

    return {
        "receipt_type": "tetra_mesh_verification",
        "mesh_id": mesh_state["mesh_id"],
        "cell_count": len(mesh_state["cells"]),
        "timestamp": datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat(),
        "canonical_hash": canonical_hash,
        "verifier_version": VERIFIER_VERSION,
        "result": result,
        "reasons": reasons,
    }
