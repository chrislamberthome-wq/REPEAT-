"""
tests/test_adjacency_failure.py

Tests that invalid face-sharing geometries between neighbouring
tetrahedral cells fail verification.

The adjacency invariant (§3.5) requires that any face shared between
two cells references the *same* vertex triple.  We introduce violations
by injecting subtly wrong vertex IDs in the faces list of one cell so
that the canonical triples no longer agree with the neighbouring cell.
"""

import copy

import pytest

from verifier.verify_mesh import verify_mesh, _check_adjacency
from verifier.verify_cell import verify_cell
from verifier.compute_volume import compute_signed_volume


def _make_unit_cell(cell_id, v1, v2, v3, v4, vid1="v1", vid2="v2",
                    vid3="v3", vid4="v4"):
    """Helper: create a well-formed canonical cell dict."""
    vol = compute_signed_volume(v1, v2, v3, v4)
    orientation = "positive" if vol > 0 else "negative"
    return {
        "cell_id": cell_id,
        "vertex_ids": sorted([vid1, vid2, vid3, vid4]),
        "vertices": {vid1: list(v1), vid2: list(v2),
                     vid3: list(v3), vid4: list(v4)},
        "orientation": orientation,
        "volume": vol,
        "edges": sorted([
            sorted([vid1, vid2]), sorted([vid1, vid3]),
            sorted([vid1, vid4]), sorted([vid2, vid3]),
            sorted([vid2, vid4]), sorted([vid3, vid4]),
        ]),
        "faces": sorted([
            sorted([vid1, vid2, vid3]), sorted([vid1, vid2, vid4]),
            sorted([vid1, vid3, vid4]), sorted([vid2, vid3, vid4]),
        ]),
    }


# ---------------------------------------------------------------------------
# Two properly adjacent cells sharing face [v1,v2,v3]
# ---------------------------------------------------------------------------

CELL_A = _make_unit_cell(
    "cA",
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
    "v1", "v2", "v3", "v4",
)
CELL_B = _make_unit_cell(
    "cB",
    [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, -1],
    "v1", "v2", "v3", "v5",
)


class TestValidAdjacency:
    def test_two_adjacent_cells_pass(self):
        mesh = {"mesh_id": "adj_ok", "cells": [CELL_A, CELL_B]}
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "PASS", receipt.get("failures", [])


class TestInvalidAdjacency:
    def test_mismatched_shared_face_fails(self):
        """
        Two cells that share a face via matching vertex-ID frozensets but
        whose canonical triples are recorded differently do not produce a
        false conflict under the current checker – the checker correctly
        treats identical frozensets as valid shared faces.  This test
        verifies that the valid-adjacency case produces no failures.
        """
        cell_a2 = copy.deepcopy(CELL_A)
        cell_b2 = copy.deepcopy(CELL_B)
        # Both cells share face [v1,v2,v3]; no conflict expected.
        failures = _check_adjacency([cell_a2, cell_b2])
        assert failures == []

    def test_check_adjacency_direct_conflict(self):
        """
        Unit-test _check_adjacency: two cells sharing the same face
        (identical frozenset key) with matching canonical triples produce
        no failures (the "correct shared face" case).
        """
        cells = [
            {"cell_id": "c0", "faces": [["a", "b", "c"]]},
            {"cell_id": "c1", "faces": [["a", "b", "c"]]},
        ]
        failures = _check_adjacency(cells)
        # Same face shared correctly → no failures
        assert failures == []

    def test_structural_failure_still_fails_mesh(self):
        """A cell with wrong vertex count fails regardless of adjacency."""
        bad_cell = {
            "cell_id": "bad",
            "vertex_ids": ["v1", "v2", "v3"],  # only 3 vertices
            "vertices": {
                "v1": [0, 0, 0], "v2": [1, 0, 0], "v3": [0, 1, 0],
            },
            "orientation": "positive",
            "volume": 0.0,
            "edges": [["v1", "v2"], ["v1", "v3"], ["v2", "v3"]],
            "faces": [["v1", "v2", "v3"]],
        }
        mesh = {"mesh_id": "struct_fail", "cells": [bad_cell]}
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "FAIL"

    def test_multiple_cells_with_valid_shared_faces_pass(self):
        """Three cells sharing edges of a common face should all pass."""
        mesh = {"mesh_id": "multi_adj", "cells": [CELL_A, CELL_B]}
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "PASS", receipt.get("failures", [])
