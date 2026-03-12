"""
tests/test_degenerate_cell.py

Tests that degenerate tetrahedra (zero or near-zero volume) are
correctly detected and produce FAIL receipts.
"""

import pytest

from verifier.compute_volume import compute_signed_volume
from verifier.verify_cell import verify_cell, VOLUME_TOLERANCE
from verifier.verify_mesh import verify_mesh


def _make_cell(v1, v2, v3, v4, orientation="positive", declared_volume=None):
    """Build a minimal cell dict for testing."""
    vol = compute_signed_volume(v1, v2, v3, v4)
    return {
        "cell_id": "c_degen",
        "vertex_ids": ["v1", "v2", "v3", "v4"],
        "vertices": {"v1": v1, "v2": v2, "v3": v3, "v4": v4},
        "orientation": orientation,
        "volume": declared_volume if declared_volume is not None else vol,
        "edges": [["v1","v2"],["v1","v3"],["v1","v4"],
                  ["v2","v3"],["v2","v4"],["v3","v4"]],
        "faces": [["v1","v2","v3"],["v1","v2","v4"],
                  ["v1","v3","v4"],["v2","v3","v4"]],
    }


class TestDegenerateVolume:
    def test_coplanar_vertices_have_zero_volume(self):
        """Four coplanar points → volume == 0."""
        vol = compute_signed_volume(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]
        )
        assert abs(vol) < 1e-12

    def test_coincident_vertices_have_zero_volume(self):
        vol = compute_signed_volume(
            [0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 1]
        )
        assert abs(vol) < 1e-12

    def test_collinear_vertices_have_zero_volume(self):
        vol = compute_signed_volume(
            [0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]
        )
        assert abs(vol) < 1e-12


class TestVerifyCellDegenerate:
    def test_coplanar_cell_fails(self):
        """All four vertices coplanar → FAIL."""
        cell = _make_cell(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
            orientation="positive",
            declared_volume=0.0,
        )
        passed, failures = verify_cell(cell)
        assert not passed
        assert any("degenerate" in f.lower() for f in failures)

    def test_coincident_cell_fails(self):
        cell = _make_cell(
            [0, 0, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0],
            orientation="positive",
            declared_volume=0.0,
        )
        passed, failures = verify_cell(cell)
        assert not passed
        assert any("degenerate" in f.lower() for f in failures)

    def test_nearly_degenerate_at_tolerance_boundary(self):
        """Volume exactly at tolerance boundary should fail."""
        # Create a near-degenerate cell with volume == VOLUME_TOLERANCE
        # by choosing v4 very close to the base plane.
        eps = VOLUME_TOLERANCE  # 1e-9
        cell = _make_cell(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, eps * 6],
            orientation="positive",
            # declared_volume is computed from the actual coords
        )
        # The computed volume will be eps (= VOLUME_TOLERANCE), which is
        # NOT strictly greater than the tolerance, so it should fail.
        computed_vol = compute_signed_volume(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, eps * 6]
        )
        assert abs(computed_vol) <= VOLUME_TOLERANCE
        passed, failures = verify_cell(cell)
        assert not passed

    def test_valid_cell_above_tolerance(self):
        """A cell clearly above the tolerance threshold must pass."""
        cell = _make_cell(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1],
            orientation="positive",
        )
        passed, failures = verify_cell(cell)
        assert passed, failures


class TestVerifyMeshDegenerate:
    def test_degenerate_cell_in_mesh_produces_fail(self):
        mesh = {
            "mesh_id": "degen_mesh",
            "cells": [
                _make_cell(
                    [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
                    orientation="positive",
                    declared_volume=0.0,
                )
            ],
        }
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "FAIL"
        assert "failures" in receipt
        assert len(receipt["failures"]) > 0

    def test_receipt_failure_mentions_degenerate(self):
        mesh = {
            "mesh_id": "degen_mesh_2",
            "cells": [
                _make_cell(
                    [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0],
                    orientation="positive",
                    declared_volume=0.0,
                )
            ],
        }
        receipt = verify_mesh(mesh)
        failures_text = " ".join(receipt["failures"]).lower()
        assert "degenerate" in failures_text
