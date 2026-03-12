"""
tests/test_orientation_failure.py

Tests that mismatches between the declared orientation and the
orientation computed from the signed volume are detected and produce
FAIL receipts.
"""

import pytest

from verifier.compute_volume import compute_signed_volume
from verifier.verify_cell import verify_cell
from verifier.verify_mesh import verify_mesh


def _make_cell(v1, v2, v3, v4, orientation, declared_volume=None):
    vol = compute_signed_volume(v1, v2, v3, v4)
    return {
        "cell_id": "c_orient",
        "vertex_ids": ["v1", "v2", "v3", "v4"],
        "vertices": {"v1": v1, "v2": v2, "v3": v3, "v4": v4},
        "orientation": orientation,
        "volume": declared_volume if declared_volume is not None else vol,
        "edges": [["v1","v2"],["v1","v3"],["v1","v4"],
                  ["v2","v3"],["v2","v4"],["v3","v4"]],
        "faces": [["v1","v2","v3"],["v1","v2","v4"],
                  ["v1","v3","v4"],["v2","v3","v4"]],
    }


# Standard unit tetrahedron vertices
V1, V2, V3, V4 = [0,0,0], [1,0,0], [0,1,0], [0,0,1]


class TestOrientationMismatch:
    def test_positive_geometry_declared_negative_fails(self):
        """Computed volume is positive but declared orientation is 'negative'."""
        cell = _make_cell(V1, V2, V3, V4, orientation="negative",
                          declared_volume=-1.0 / 6.0)
        passed, failures = verify_cell(cell)
        assert not passed
        assert any("orientation" in f.lower() for f in failures)

    def test_negative_geometry_declared_positive_fails(self):
        """Swapped vertices give negative volume; declared 'positive' → fail."""
        cell = _make_cell(V1, V3, V2, V4, orientation="positive",
                          declared_volume=1.0 / 6.0)
        passed, failures = verify_cell(cell)
        assert not passed
        assert any("orientation" in f.lower() for f in failures)

    def test_correct_positive_orientation_passes(self):
        vol = compute_signed_volume(V1, V2, V3, V4)
        cell = _make_cell(V1, V2, V3, V4, orientation="positive",
                          declared_volume=vol)
        passed, failures = verify_cell(cell)
        assert passed, failures

    def test_correct_negative_orientation_passes(self):
        """Swapped vertices → negative volume → declared 'negative' → pass."""
        vol = compute_signed_volume(V1, V3, V2, V4)
        assert vol < 0
        cell = _make_cell(V1, V3, V2, V4, orientation="negative",
                          declared_volume=vol)
        passed, failures = verify_cell(cell)
        assert passed, failures

    def test_unknown_orientation_value_fails(self):
        cell = _make_cell(V1, V2, V3, V4, orientation="sideways")
        passed, failures = verify_cell(cell)
        assert not passed
        assert any("orientation" in f.lower() for f in failures)


class TestOrientationFailureInMesh:
    def test_orientation_mismatch_produces_fail_receipt(self):
        mesh = {
            "mesh_id": "orient_fail_mesh",
            "cells": [
                _make_cell(V1, V2, V3, V4, orientation="negative",
                           declared_volume=-1.0 / 6.0)
            ],
        }
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "FAIL"
        assert "failures" in receipt

    def test_failure_message_mentions_orientation(self):
        mesh = {
            "mesh_id": "orient_fail_mesh_2",
            "cells": [
                _make_cell(V1, V2, V3, V4, orientation="negative",
                           declared_volume=-1.0 / 6.0)
            ],
        }
        receipt = verify_mesh(mesh)
        failures_text = " ".join(receipt["failures"]).lower()
        assert "orientation" in failures_text

    def test_correct_orientation_produces_pass_receipt(self):
        vol = compute_signed_volume(V1, V2, V3, V4)
        mesh = {
            "mesh_id": "orient_pass_mesh",
            "cells": [
                _make_cell(V1, V2, V3, V4, orientation="positive",
                           declared_volume=vol)
            ],
        }
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "PASS"
