"""
tests/test_valid_mesh.py

Tests that valid tetrahedral meshes produce PASS receipts and that
canonicalisation and hashing are deterministic.
"""

import hashlib
import json

import pytest

from verifier.canonicalize_mesh import canonical_json, canonicalize_mesh
from verifier.compute_volume import compute_signed_volume
from verifier.verify_cell import verify_cell
from verifier.verify_mesh import verify_mesh

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

UNIT_TETRA = {
    "cell_id": "c0",
    "vertex_ids": ["v1", "v2", "v3", "v4"],
    "vertices": {
        "v1": [0.0, 0.0, 0.0],
        "v2": [1.0, 0.0, 0.0],
        "v3": [0.0, 1.0, 0.0],
        "v4": [0.0, 0.0, 1.0],
    },
    "orientation": "positive",
    "volume": 1.0 / 6.0,
    "edges": [
        ["v1", "v2"], ["v1", "v3"], ["v1", "v4"],
        ["v2", "v3"], ["v2", "v4"], ["v3", "v4"],
    ],
    "faces": [
        ["v1", "v2", "v3"], ["v1", "v2", "v4"],
        ["v1", "v3", "v4"], ["v2", "v3", "v4"],
    ],
}

VALID_MESH = {
    "mesh_id": "mesh_001",
    "cells": [UNIT_TETRA],
}


# ---------------------------------------------------------------------------
# Volume computation
# ---------------------------------------------------------------------------

class TestComputeSignedVolume:
    def test_unit_tetrahedron_volume(self):
        v = compute_signed_volume(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
        )
        assert abs(v - 1.0 / 6.0) < 1e-12

    def test_negative_orientation(self):
        # Swap two vertices to flip orientation
        v = compute_signed_volume(
            [0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]
        )
        assert v < 0

    def test_volume_symmetry(self):
        v_pos = compute_signed_volume(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]
        )
        v_neg = compute_signed_volume(
            [0, 0, 0], [0, 1, 0], [1, 0, 0], [0, 0, 1]
        )
        assert abs(abs(v_pos) - abs(v_neg)) < 1e-12


# ---------------------------------------------------------------------------
# Per-cell verification
# ---------------------------------------------------------------------------

class TestVerifyCell:
    def test_valid_cell_passes(self):
        passed, failures = verify_cell(UNIT_TETRA)
        assert passed
        assert failures == []

    def test_cell_with_correct_structure(self):
        passed, failures = verify_cell(UNIT_TETRA)
        assert passed

    def test_cell_returns_bool_and_list(self):
        result = verify_cell(UNIT_TETRA)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)


# ---------------------------------------------------------------------------
# Canonicalisation
# ---------------------------------------------------------------------------

class TestCanonicalizeMesh:
    def test_canonical_json_is_deterministic(self):
        j1 = canonical_json(VALID_MESH)
        j2 = canonical_json(VALID_MESH)
        assert j1 == j2

    def test_canonical_json_is_valid_json(self):
        j = canonical_json(VALID_MESH)
        parsed = json.loads(j)
        assert parsed["mesh_id"] == "mesh_001"

    def test_unsorted_vertex_ids_get_sorted(self):
        mesh = {
            "mesh_id": "m",
            "cells": [{
                "cell_id": "c",
                "vertex_ids": ["v4", "v3", "v2", "v1"],
                "vertices": {
                    "v1": [0.0, 0.0, 0.0],
                    "v2": [1.0, 0.0, 0.0],
                    "v3": [0.0, 1.0, 0.0],
                    "v4": [0.0, 0.0, 1.0],
                },
                "orientation": "positive",
                "volume": 1.0 / 6.0,
                "edges": [["v1","v2"],["v1","v3"],["v1","v4"],
                           ["v2","v3"],["v2","v4"],["v3","v4"]],
                "faces": [["v1","v2","v3"],["v1","v2","v4"],
                           ["v1","v3","v4"],["v2","v3","v4"]],
            }],
        }
        canonical = canonicalize_mesh(mesh)
        assert canonical["cells"][0]["vertex_ids"] == ["v1", "v2", "v3", "v4"]

    def test_canonical_hash_is_sha256(self):
        j = canonical_json(VALID_MESH)
        expected = hashlib.sha256(j.encode("utf-8")).hexdigest()
        assert len(expected) == 64
        assert all(c in "0123456789abcdef" for c in expected)


# ---------------------------------------------------------------------------
# Full mesh verification
# ---------------------------------------------------------------------------

class TestVerifyMesh:
    def test_valid_mesh_passes(self):
        receipt = verify_mesh(VALID_MESH)
        assert receipt["result"] == "PASS"

    def test_receipt_has_required_fields(self):
        receipt = verify_mesh(VALID_MESH)
        for field in ("receipt_type", "mesh_id", "cell_count",
                      "timestamp", "canonical_hash", "verifier_version", "result"):
            assert field in receipt, f"Missing field: {field}"

    def test_receipt_type(self):
        receipt = verify_mesh(VALID_MESH)
        assert receipt["receipt_type"] == "tetra_mesh_verification"

    def test_receipt_mesh_id(self):
        receipt = verify_mesh(VALID_MESH)
        assert receipt["mesh_id"] == "mesh_001"

    def test_receipt_cell_count(self):
        receipt = verify_mesh(VALID_MESH)
        assert receipt["cell_count"] == 1

    def test_receipt_verifier_version(self):
        receipt = verify_mesh(VALID_MESH)
        assert receipt["verifier_version"] == "tmp_v1"

    def test_canonical_hash_is_hex(self):
        receipt = verify_mesh(VALID_MESH)
        h = receipt["canonical_hash"]
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_canonical_hash_is_deterministic(self):
        r1 = verify_mesh(VALID_MESH)
        r2 = verify_mesh(VALID_MESH)
        assert r1["canonical_hash"] == r2["canonical_hash"]

    def test_prev_receipt_hash_propagated(self):
        prev = "a" * 64
        receipt = verify_mesh(VALID_MESH, prev_receipt_hash=prev)
        assert receipt["prev_receipt_hash"] == prev

    def test_no_failures_field_on_pass(self):
        receipt = verify_mesh(VALID_MESH)
        assert "failures" not in receipt or receipt["failures"] == []

    def test_multi_cell_mesh_passes(self):
        cell_b = {
            "cell_id": "c1",
            "vertex_ids": ["v1", "v2", "v3", "v5"],
            "vertices": {
                "v1": [0.0, 0.0, 0.0],
                "v2": [1.0, 0.0, 0.0],
                "v3": [0.0, 1.0, 0.0],
                "v5": [0.0, 0.0, -1.0],
            },
            "orientation": "negative",
            "volume": -1.0 / 6.0,
            "edges": [["v1","v2"],["v1","v3"],["v1","v5"],
                       ["v2","v3"],["v2","v5"],["v3","v5"]],
            "faces": [["v1","v2","v3"],["v1","v2","v5"],
                       ["v1","v3","v5"],["v2","v3","v5"]],
        }
        mesh = {"mesh_id": "mesh_002", "cells": [UNIT_TETRA, cell_b]}
        receipt = verify_mesh(mesh)
        assert receipt["result"] == "PASS"
        assert receipt["cell_count"] == 2
