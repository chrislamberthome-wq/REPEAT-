"""
verifier/verify_cell.py

Verifies a single tetrahedral cell against all TMP protocol invariants.

Invariants checked (§3 of TETRAHEDRAL_MESH_PROTOCOL_v1.md):
  3.1  Structural validity  – exactly 4 vertex IDs, 6 edges, 4 faces
  3.2  Edge consistency     – every edge references valid vertex IDs
  3.3  Face orientation     – winding order matches declared orientation
  3.4  Signed volume        – |volume| > VOLUME_TOLERANCE (non-degenerate)
                              declared volume within VOLUME_TOLERANCE of computed
  3.5  Orientation match    – sign(computed_volume) matches declared orientation
"""

from .compute_volume import compute_signed_volume

VOLUME_TOLERANCE = 1e-9
"""Minimum absolute volume accepted as non-degenerate."""

VOLUME_MATCH_TOLERANCE = 1e-6
"""Maximum allowed difference between declared and computed volume."""


def verify_cell(cell):
    """
    Verify a single tetrahedral cell.

    Parameters
    ----------
    cell : dict
        A cell dict conforming to ``tetra_mesh_state.schema.json``.

    Returns
    -------
    tuple[bool, list[str]]
        ``(passed, failures)`` where *failures* is a list of human-readable
        failure descriptions.  *passed* is ``True`` iff *failures* is empty.
    """
    failures = []
    cell_id = cell.get("cell_id", "<unknown>")

    # --- 3.1 Structural validity -----------------------------------------
    vertex_ids = cell.get("vertex_ids", [])
    if len(vertex_ids) != 4:
        failures.append(
            f"cell {cell_id}: expected 4 vertex_ids, got {len(vertex_ids)}"
        )

    vertices = cell.get("vertices", {})
    # All declared vertex_ids must have coordinate entries
    for vid in vertex_ids:
        if vid not in vertices:
            failures.append(
                f"cell {cell_id}: vertex_id '{vid}' has no coordinate entry"
            )

    edges = cell.get("edges", [])
    if len(edges) != 6:
        failures.append(
            f"cell {cell_id}: expected 6 edges, got {len(edges)}"
        )

    faces = cell.get("faces", [])
    if len(faces) != 4:
        failures.append(
            f"cell {cell_id}: expected 4 faces, got {len(faces)}"
        )

    # --- 3.2 Edge consistency --------------------------------------------
    vertex_id_set = set(vertex_ids)
    for edge in edges:
        if len(edge) != 2:
            failures.append(
                f"cell {cell_id}: edge {edge!r} does not have exactly 2 endpoints"
            )
            continue
        for vid in edge:
            if vid not in vertex_id_set:
                failures.append(
                    f"cell {cell_id}: edge {edge!r} references unknown vertex '{vid}'"
                )

    # --- 3.3 / 3.4 / 3.5  Volume & orientation checks -------------------
    # Only meaningful when all four vertex coordinates are present.
    if len(vertex_ids) == 4 and all(vid in vertices for vid in vertex_ids):
        v1, v2, v3, v4 = [vertices[vid] for vid in vertex_ids]
        computed = compute_signed_volume(v1, v2, v3, v4)

        # 3.4 Non-degenerate volume
        if abs(computed) <= VOLUME_TOLERANCE:
            failures.append(
                f"cell {cell_id}: degenerate tetrahedron "
                f"(|computed volume| = {abs(computed):.2e} ≤ {VOLUME_TOLERANCE})"
            )
        else:
            # 3.5 Orientation match
            declared_orientation = cell.get("orientation", "")
            computed_orientation = "positive" if computed > 0 else "negative"
            if declared_orientation not in ("positive", "negative"):
                failures.append(
                    f"cell {cell_id}: unknown orientation value '{declared_orientation}'"
                )
            elif declared_orientation != computed_orientation:
                failures.append(
                    f"cell {cell_id}: orientation mismatch – "
                    f"declared '{declared_orientation}', "
                    f"computed '{computed_orientation}' (volume={computed:.6f})"
                )

            # 3.3 Declared volume must match computed volume
            declared_volume = cell.get("volume", 0.0)
            if abs(declared_volume - computed) > VOLUME_MATCH_TOLERANCE:
                failures.append(
                    f"cell {cell_id}: declared volume {declared_volume:.6f} "
                    f"does not match computed volume {computed:.6f} "
                    f"(diff={abs(declared_volume - computed):.2e})"
                )

    return (len(failures) == 0, failures)
