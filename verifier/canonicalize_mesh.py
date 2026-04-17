"""
verifier/canonicalize_mesh.py

Canonicalises a raw tetrahedral mesh state dictionary so that
identical geometric configurations always produce identical JSON
representations, regardless of the order in which vertices, edges,
or cells were originally specified.

Canonicalisation rules (from TETRAHEDRAL_MESH_PROTOCOL_v1.md):
  - vertex_ids are sorted lexicographically
  - vertex coordinate values are rounded to a fixed decimal precision
  - edge pairs are sorted (smaller ID first), then the edge list is sorted
  - face triples are sorted (IDs within each triple), then the face list is sorted
  - JSON keys are lexicographically sorted
  - Output encoding is UTF-8
"""

import json

COORDINATE_PRECISION = 10
"""Number of decimal places to which vertex coordinates are rounded."""


def _round_coord(coord, precision=COORDINATE_PRECISION):
    """Return a coordinate triple with each component rounded."""
    return [round(float(v), precision) for v in coord]


def _canonical_edge(v1, v2):
    """Return a canonical (sorted) edge pair as a list."""
    return sorted([v1, v2])


def _canonical_face(v1, v2, v3):
    """Return a canonical (sorted) face triple as a list."""
    return sorted([v1, v2, v3])


def _canonical_cell(cell):
    """
    Return a canonicalised copy of a single tetrahedral cell dict.

    The function:
      1. Sorts vertex_ids lexicographically.
      2. Rounds all vertex coordinates (for IDs that have entries).
      3. Rebuilds the canonical edge and face lists when exactly 4 vertex
         IDs are present; otherwise preserves existing lists so that
         verify_cell can emit the appropriate structural-validity failure.
      4. Preserves orientation and volume as declared.
    """
    vertex_ids = sorted(cell["vertex_ids"])
    vertices = {
        vid: _round_coord(cell["vertices"][vid])
        for vid in vertex_ids
        if vid in cell.get("vertices", {})
    }

    if len(vertex_ids) == 4:
        v1, v2, v3, v4 = vertex_ids

        edges = sorted([
            _canonical_edge(v1, v2),
            _canonical_edge(v1, v3),
            _canonical_edge(v1, v4),
            _canonical_edge(v2, v3),
            _canonical_edge(v2, v4),
            _canonical_edge(v3, v4),
        ])

        faces = sorted([
            _canonical_face(v1, v2, v3),
            _canonical_face(v1, v2, v4),
            _canonical_face(v1, v3, v4),
            _canonical_face(v2, v3, v4),
        ])
    else:
        # Wrong number of vertices – preserve whatever was declared so that
        # verify_cell can detect and report the structural-validity failure.
        edges = sorted(
            sorted(e) for e in cell.get("edges", [])
        )
        faces = sorted(
            sorted(f) for f in cell.get("faces", [])
        )

    return {
        "cell_id": cell["cell_id"],
        "edges": edges,
        "faces": faces,
        "orientation": cell["orientation"],
        "vertex_ids": vertex_ids,
        "vertices": vertices,
        "volume": round(float(cell["volume"]), COORDINATE_PRECISION),
    }


def canonicalize_mesh(mesh_state):
    """
    Return a canonicalised copy of *mesh_state*.

    Parameters
    ----------
    mesh_state : dict
        A raw (possibly unsorted) mesh state conforming to
        ``tetra_mesh_state.schema.json``.

    Returns
    -------
    dict
        A new dict whose keys are lexicographically ordered and whose
        cell entries are fully canonicalised.  The original dict is
        not modified.
    """
    cells = sorted(
        [_canonical_cell(c) for c in mesh_state["cells"]],
        key=lambda c: c["cell_id"],
    )
    return {
        "cells": cells,
        "mesh_id": mesh_state["mesh_id"],
    }


def canonical_json(mesh_state):
    """
    Return the UTF-8 canonical JSON string for *mesh_state*.

    The string uses compact separators, sorted keys, and rounded
    coordinates so that the same geometry always produces the same
    byte sequence.

    Parameters
    ----------
    mesh_state : dict
        Raw or already-canonicalised mesh state.

    Returns
    -------
    str
        Canonical JSON string (UTF-8 safe, no trailing newline).
    """
    canonical = canonicalize_mesh(mesh_state)
    return json.dumps(
        canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
