from __future__ import annotations

from typing import Any

from .compute_volume import compute_signed_volume

DEFAULT_TOLERANCE = 1e-12


def verify_cell(cell: dict[str, Any], tolerance: float = DEFAULT_TOLERANCE) -> tuple:
    reasons: list = []

    vertex_ids = cell.get("vertex_ids", [])
    vertices = cell.get("vertices", {})
    orientation = cell.get("orientation")

    if len(vertex_ids) != 4:
        reasons.append("vertex_ids must contain exactly 4 items")
        return False, reasons

    if sorted(vertex_ids) != sorted(vertices.keys()):
        reasons.append("vertex_ids and vertices keys mismatch")
        return False, reasons

    v1, v2, v3, v4 = [vertices[vid] for vid in vertex_ids]
    volume = compute_signed_volume(v1, v2, v3, v4)

    if abs(volume) <= tolerance:
        reasons.append("degenerate tetrahedron: signed volume is zero within tolerance")

    expected_orientation = "positive" if volume > 0 else "negative"
    if abs(volume) > tolerance and orientation != expected_orientation:
        reasons.append(
            f"orientation mismatch: declared={orientation} computed={expected_orientation}"
        )

    return len(reasons) == 0, reasons
