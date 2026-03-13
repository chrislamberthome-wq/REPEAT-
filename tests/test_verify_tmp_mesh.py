"""Tests for the TMP v1 reference verifier (verify_tmp_mesh.py)."""

import json
import os
import sys
import tempfile
import pytest

# Ensure the verifier module is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from verifier.verify_tmp_mesh import (
    EXIT_ERROR,
    EXIT_FAIL,
    EXIT_PASS,
    canonical_json,
    check_topology,
    compute_canonical_hash,
    faces_opposite_orientation,
    get_face_vertices,
    load_json,
    normalize_mesh_for_canonicalization,
    normalize_tetra_vertices,
    topology_projection,
    validate_schema,
    verify,
)

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _golden(name: str) -> str:
    return os.path.join(GOLDEN_DIR, name)


def _write_tmp(data: dict) -> str:
    """Write a dict to a temp JSON file; caller must delete it."""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    return path


def _minimal_tet() -> dict:
    """Return a valid minimal single-tetrahedron mesh."""
    return {
        "protocol": "TMP-v1",
        "version": "1.0.0",
        "mesh_id": "test-tet",
        "vertex_ids": ["v0", "v1", "v2", "v3"],
        "tetrahedra": [{"tetra_id": "T0", "vertices": ["v0", "v1", "v2", "v3"]}],
        "adjacency": [],
        "boundary_faces": [
            {"tetra_id": "T0", "face": 0},
            {"tetra_id": "T0", "face": 1},
            {"tetra_id": "T0", "face": 2},
            {"tetra_id": "T0", "face": 3},
        ],
        "orientation_rule": "right_hand_outward",
        "canonicalization_version": "c14n-v1",
        "declared_invariants": [],
    }


# ---------------------------------------------------------------------------
# Golden file tests
# ---------------------------------------------------------------------------

class TestGoldenPASS:
    """Golden PASS examples must produce verdict PASS and exit code 0."""

    def test_pass_minimal_tet(self):
        verdict, exit_code, receipt = verify(_golden("pass_minimal_tet.json"))
        assert verdict == "PASS"
        assert exit_code == EXIT_PASS
        assert receipt["verdict"] == "PASS"
        assert receipt["vertex_count"] == 4
        assert receipt["tetra_count"] == 1
        assert receipt["adjacency_count"] == 0
        assert receipt["boundary_face_count"] == 4
        assert receipt["canonical_sha256"].startswith("sha256:")

    def test_pass_cube_5tet(self):
        verdict, exit_code, receipt = verify(_golden("pass_cube_5tet.json"))
        assert verdict == "PASS"
        assert exit_code == EXIT_PASS
        assert receipt["verdict"] == "PASS"
        assert receipt["vertex_count"] == 8
        assert receipt["tetra_count"] == 5
        assert receipt["adjacency_count"] == 4
        assert receipt["boundary_face_count"] == 12

    def test_pass_minimal_tet_hash_matches_declared(self):
        """The computed hash must match the declared topology_hash."""
        with open(_golden("pass_minimal_tet.json")) as f:
            mesh = json.load(f)
        computed = compute_canonical_hash(mesh)
        assert computed == mesh["topology_hash"]

    def test_pass_cube_5tet_hash_matches_declared(self):
        with open(_golden("pass_cube_5tet.json")) as f:
            mesh = json.load(f)
        computed = compute_canonical_hash(mesh)
        assert computed == mesh["topology_hash"]


class TestGoldenFAIL:
    """Golden FAIL examples must produce verdict FAIL and exit code 1."""

    def test_fail_duplicate_tet(self):
        verdict, exit_code, receipt = verify(_golden("fail_duplicate_tet.json"))
        assert verdict == "FAIL"
        assert exit_code == EXIT_FAIL
        assert receipt["verdict"] == "FAIL"
        assert "fail_reasons" in receipt
        assert any("uplicate" in r for r in receipt["fail_reasons"])

    def test_fail_broken_adjacency(self):
        verdict, exit_code, receipt = verify(_golden("fail_broken_adjacency.json"))
        assert verdict == "FAIL"
        assert exit_code == EXIT_FAIL
        assert receipt["verdict"] == "FAIL"
        assert "fail_reasons" in receipt
        assert any("mismatch" in r for r in receipt["fail_reasons"])

    def test_fail_boundary_mismatch(self):
        verdict, exit_code, receipt = verify(_golden("fail_boundary_mismatch.json"))
        assert verdict == "FAIL"
        assert exit_code == EXIT_FAIL
        assert receipt["verdict"] == "FAIL"
        assert "fail_reasons" in receipt
        assert any("accounting" in r or "face" in r.lower() for r in receipt["fail_reasons"])


class TestGoldenERROR:
    """Golden ERROR examples must produce verdict ERROR and exit code 2."""

    def test_error_malformed_schema(self):
        verdict, exit_code, receipt = verify(_golden("error_malformed_schema.json"))
        assert verdict == "ERROR"
        assert exit_code == EXIT_ERROR
        assert receipt["verdict"] == "ERROR"
        assert "schema_errors" in receipt
        assert len(receipt["schema_errors"]) > 0

    def test_error_file_not_found(self):
        verdict, exit_code, receipt = verify("/nonexistent/path/mesh.json")
        assert verdict == "ERROR"
        assert exit_code == EXIT_ERROR
        assert "error" in receipt

    def test_error_invalid_json(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("{not valid json")
            verdict, exit_code, receipt = verify(path)
            assert verdict == "ERROR"
            assert exit_code == EXIT_ERROR
        finally:
            os.unlink(path)

    def test_error_non_object_json(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("[1, 2, 3]")
            verdict, exit_code, receipt = verify(path)
            assert verdict == "ERROR"
            assert exit_code == EXIT_ERROR
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Schema validation unit tests
# ---------------------------------------------------------------------------

class TestValidateSchema:
    """Unit tests for validate_schema()."""

    def test_valid_minimal(self):
        mesh = _minimal_tet()
        errors = validate_schema(mesh)
        assert errors == []

    def test_missing_protocol(self):
        mesh = _minimal_tet()
        del mesh["protocol"]
        errors = validate_schema(mesh)
        assert any("protocol" in e for e in errors)

    def test_wrong_protocol(self):
        mesh = _minimal_tet()
        mesh["protocol"] = "TMP-v2"
        errors = validate_schema(mesh)
        assert any("protocol" in e for e in errors)

    def test_bad_version(self):
        mesh = _minimal_tet()
        mesh["version"] = "1.0"
        errors = validate_schema(mesh)
        assert any("version" in e for e in errors)

    def test_empty_mesh_id(self):
        mesh = _minimal_tet()
        mesh["mesh_id"] = ""
        errors = validate_schema(mesh)
        assert any("mesh_id" in e for e in errors)

    def test_too_few_vertex_ids(self):
        mesh = _minimal_tet()
        mesh["vertex_ids"] = ["v0", "v1", "v2"]
        errors = validate_schema(mesh)
        assert any("vertex_ids" in e for e in errors)

    def test_duplicate_vertex_ids(self):
        mesh = _minimal_tet()
        mesh["vertex_ids"] = ["v0", "v1", "v2", "v0"]
        errors = validate_schema(mesh)
        assert any("unique" in e.lower() for e in errors)

    def test_wrong_orientation_rule(self):
        mesh = _minimal_tet()
        mesh["orientation_rule"] = "left_hand"
        errors = validate_schema(mesh)
        assert any("orientation_rule" in e for e in errors)

    def test_wrong_canonicalization_version(self):
        mesh = _minimal_tet()
        mesh["canonicalization_version"] = "c14n-v2"
        errors = validate_schema(mesh)
        assert any("canonicalization_version" in e for e in errors)

    def test_unknown_invariant(self):
        mesh = _minimal_tet()
        mesh["declared_invariants"] = ["unknown_check"]
        errors = validate_schema(mesh)
        assert any("unknown_invariant" in e.lower() or "unknown" in e.lower() for e in errors)

    def test_topology_hash_bad_format(self):
        mesh = _minimal_tet()
        mesh["topology_hash"] = "notahash"
        errors = validate_schema(mesh)
        assert any("topology_hash" in e for e in errors)

    def test_topology_hash_valid_format(self):
        mesh = _minimal_tet()
        mesh["topology_hash"] = "sha256:" + "a" * 64
        errors = validate_schema(mesh)
        assert errors == []

    def test_tetra_with_wrong_vertex_count(self):
        mesh = _minimal_tet()
        mesh["tetrahedra"][0]["vertices"] = ["v0", "v1", "v2"]
        errors = validate_schema(mesh)
        assert any("4" in e or "vertices" in e for e in errors)

    def test_face_ref_out_of_range(self):
        mesh = _minimal_tet()
        mesh["adjacency"] = [
            {"left": {"tetra_id": "T0", "face": 4}, "right": {"tetra_id": "T0", "face": 0}}
        ]
        errors = validate_schema(mesh)
        assert any("face" in e.lower() for e in errors)

    def test_face_ref_negative(self):
        mesh = _minimal_tet()
        mesh["adjacency"] = [
            {"left": {"tetra_id": "T0", "face": -1}, "right": {"tetra_id": "T0", "face": 0}}
        ]
        errors = validate_schema(mesh)
        assert any("face" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Topology check unit tests
# ---------------------------------------------------------------------------

class TestCheckTopology:
    """Unit tests for check_topology()."""

    def test_valid_minimal_tet(self):
        mesh = _minimal_tet()
        fails, warns = check_topology(mesh)
        assert fails == []

    def test_non_distinct_vertices(self):
        mesh = _minimal_tet()
        mesh["tetrahedra"][0]["vertices"] = ["v0", "v0", "v1", "v2"]
        fails, warns = check_topology(mesh)
        assert any("distinct" in f for f in fails)

    def test_vertex_not_in_vertex_ids(self):
        mesh = _minimal_tet()
        mesh["tetrahedra"][0]["vertices"] = ["v0", "v1", "v2", "vX"]
        fails, warns = check_topology(mesh)
        assert any("vX" in f for f in fails)

    def test_duplicate_tetrahedra(self):
        mesh = _minimal_tet()
        mesh["vertex_ids"] = ["v0", "v1", "v2", "v3"]
        # Add a second tetra with same vertices but different id, adjust boundary
        mesh["tetrahedra"].append({"tetra_id": "T1", "vertices": ["v0", "v1", "v2", "v3"]})
        mesh["boundary_faces"].extend([
            {"tetra_id": "T1", "face": 0},
            {"tetra_id": "T1", "face": 1},
            {"tetra_id": "T1", "face": 2},
            {"tetra_id": "T1", "face": 3},
        ])
        fails, warns = check_topology(mesh)
        assert any("uplicate" in f for f in fails)

    def test_face_accounting_mismatch(self):
        mesh = _minimal_tet()
        # Remove one boundary face — creates mismatch
        mesh["boundary_faces"] = mesh["boundary_faces"][:3]
        fails, warns = check_topology(mesh)
        assert any("accounting" in f.lower() or "mismatch" in f.lower() for f in fails)

    def test_adjacency_unknown_tetra(self):
        # Two distinct tetras; adjacency references a non-existent tetra.
        # Face accounting: 2 tetras × 4 = 8 = 1 adj × 2 + 6 boundary (T0:3, T1:3)
        # T1.face3 will also be unaccounted, but T_UNKNOWN must appear in fails.
        mesh = {
            "protocol": "TMP-v1",
            "version": "1.0.0",
            "mesh_id": "test",
            "vertex_ids": ["v0", "v1", "v2", "v3", "v4"],
            "tetrahedra": [
                {"tetra_id": "T0", "vertices": ["v0", "v1", "v2", "v3"]},
                {"tetra_id": "T1", "vertices": ["v0", "v2", "v1", "v4"]},
            ],
            # T0.face3 claimed against T_UNKNOWN (does not exist)
            "adjacency": [
                {"left": {"tetra_id": "T0", "face": 3},
                 "right": {"tetra_id": "T_UNKNOWN", "face": 0}}
            ],
            # 6 boundary faces: T0 faces 0,1,2 and T1 faces 0,1,2
            # (accounts for 8 = 1*2 + 6; T1.face3 left unaccounted on purpose)
            "boundary_faces": [
                {"tetra_id": "T0", "face": 0},
                {"tetra_id": "T0", "face": 1},
                {"tetra_id": "T0", "face": 2},
                {"tetra_id": "T1", "face": 0},
                {"tetra_id": "T1", "face": 1},
                {"tetra_id": "T1", "face": 2},
            ],
            "orientation_rule": "right_hand_outward",
            "canonicalization_version": "c14n-v1",
            "declared_invariants": [],
        }
        fails, warns = check_topology(mesh)
        assert any("T_UNKNOWN" in f for f in fails)

    def test_face_used_twice(self):
        mesh = _minimal_tet()
        # Claim face 0 in both adjacency and boundary
        mesh["boundary_faces"] = [
            {"tetra_id": "T0", "face": 0},  # duplicate
            {"tetra_id": "T0", "face": 0},
            {"tetra_id": "T0", "face": 1},
            {"tetra_id": "T0", "face": 2},
        ]
        fails, warns = check_topology(mesh)
        assert len(fails) > 0

    def test_adjacency_vertex_mismatch(self):
        """Adjacency declares two faces that don't share the same vertex set."""
        mesh = {
            "protocol": "TMP-v1",
            "version": "1.0.0",
            "mesh_id": "test",
            "vertex_ids": ["v0", "v1", "v2", "v3", "v4"],
            "tetrahedra": [
                {"tetra_id": "T0", "vertices": ["v0", "v1", "v2", "v3"]},
                {"tetra_id": "T1", "vertices": ["v0", "v1", "v2", "v4"]},
            ],
            "adjacency": [
                # T0.face3=(v0,v1,v2) ↔ T1.face2=(v0,v1,v4) — vertex-set mismatch
                {"left": {"tetra_id": "T0", "face": 3}, "right": {"tetra_id": "T1", "face": 2}}
            ],
            "boundary_faces": [
                {"tetra_id": "T0", "face": 0},
                {"tetra_id": "T0", "face": 1},
                {"tetra_id": "T0", "face": 2},
                {"tetra_id": "T1", "face": 0},
                {"tetra_id": "T1", "face": 1},
                {"tetra_id": "T1", "face": 3},
            ],
            "orientation_rule": "right_hand_outward",
            "canonicalization_version": "c14n-v1",
            "declared_invariants": [],
        }
        fails, warns = check_topology(mesh)
        assert any("mismatch" in f.lower() for f in fails)

    def test_connected_invariant_pass(self):
        mesh = _minimal_tet()
        mesh["declared_invariants"] = ["connected"]
        fails, warns = check_topology(mesh)
        assert fails == []

    def test_closed_boundary_invariant_pass(self):
        mesh = _minimal_tet()
        mesh["declared_invariants"] = ["closed_boundary"]
        fails, warns = check_topology(mesh)
        assert fails == []

    def test_orientation_invariant_no_check_when_not_declared(self):
        """Orientation issues are warnings, not failures, if 'oriented' not declared."""
        mesh = _minimal_tet()
        mesh["declared_invariants"] = []
        fails, warns = check_topology(mesh)
        assert fails == []


# ---------------------------------------------------------------------------
# Canonicalization unit tests
# ---------------------------------------------------------------------------

class TestCanonicalJson:
    """Unit tests for canonical_json()."""

    def test_empty_object(self):
        assert canonical_json({}) == b"{}"

    def test_empty_array(self):
        assert canonical_json([]) == b"[]"

    def test_sorted_keys(self):
        result = canonical_json({"b": 1, "a": 2})
        assert result == b'{"a":2,"b":1}'

    def test_nested_sorted_keys(self):
        result = canonical_json({"z": {"b": 1, "a": 2}})
        assert result == b'{"z":{"a":2,"b":1}}'

    def test_no_whitespace(self):
        result = canonical_json({"key": "value"})
        assert b" " not in result

    def test_bool_values(self):
        assert canonical_json(True) == b"true"
        assert canonical_json(False) == b"false"

    def test_null(self):
        assert canonical_json(None) == b"null"

    def test_integer(self):
        assert canonical_json(42) == b"42"

    def test_string_utf8(self):
        result = canonical_json("hello")
        assert result == b'"hello"'

    def test_array_preserves_order(self):
        result = canonical_json([3, 1, 2])
        assert result == b"[3,1,2]"


class TestNormalizeTetraVertices:
    """Unit tests for normalize_tetra_vertices()."""

    def test_already_minimal(self):
        verts = ["v0", "v1", "v2", "v3"]
        result = normalize_tetra_vertices(verts)
        # Result must be an even permutation with v0 first
        assert result[0] == "v0"
        assert set(result) == set(verts)

    def test_non_minimal_start(self):
        verts = ["v3", "v2", "v1", "v0"]
        result = normalize_tetra_vertices(verts)
        # Result should start with the smallest
        assert result[0] == "v0"

    def test_preserves_vertex_set(self):
        verts = ["v1", "v0", "v3", "v2"]
        result = normalize_tetra_vertices(verts)
        assert sorted(result) == sorted(verts)

    def test_idempotent(self):
        verts = ["v0", "v1", "v2", "v3"]
        once = normalize_tetra_vertices(verts)
        twice = normalize_tetra_vertices(once)
        assert once == twice


class TestComputeCanonicalHash:
    """Unit tests for compute_canonical_hash()."""

    def test_returns_sha256_prefix(self):
        mesh = _minimal_tet()
        h = compute_canonical_hash(mesh)
        assert h.startswith("sha256:")
        assert len(h) == len("sha256:") + 64

    def test_deterministic(self):
        mesh = _minimal_tet()
        h1 = compute_canonical_hash(mesh)
        h2 = compute_canonical_hash(mesh)
        assert h1 == h2

    def test_geometry_excluded_from_hash(self):
        mesh1 = _minimal_tet()
        mesh2 = _minimal_tet()
        mesh2["geometry"] = {
            "coordinate_system": "euclidean_3d",
            "coordinates": {
                "v0": [0.0, 0.0, 0.0],
                "v1": [1.0, 0.0, 0.0],
                "v2": [0.0, 1.0, 0.0],
                "v3": [0.0, 0.0, 1.0],
            },
        }
        assert compute_canonical_hash(mesh1) == compute_canonical_hash(mesh2)

    def test_different_mesh_ids_differ(self):
        mesh1 = _minimal_tet()
        mesh2 = _minimal_tet()
        mesh2["mesh_id"] = "different-id"
        assert compute_canonical_hash(mesh1) != compute_canonical_hash(mesh2)

    def test_matches_golden_minimal_tet(self):
        with open(_golden("pass_minimal_tet.json")) as f:
            golden = json.load(f)
        expected = golden["topology_hash"]
        mesh = _minimal_tet()
        mesh["mesh_id"] = golden["mesh_id"]
        mesh["declared_invariants"] = golden["declared_invariants"]
        assert compute_canonical_hash(mesh) == expected


class TestNormalizeMeshForCanonicalization:
    """Unit tests for normalize_mesh_for_canonicalization()."""

    def test_vertex_ids_sorted(self):
        mesh = _minimal_tet()
        mesh["vertex_ids"] = ["v3", "v1", "v0", "v2"]
        normalized = normalize_mesh_for_canonicalization(mesh)
        assert normalized["vertex_ids"] == sorted(mesh["vertex_ids"])

    def test_invariants_sorted(self):
        mesh = _minimal_tet()
        mesh["declared_invariants"] = ["manifold_interior", "closed_boundary", "connected"]
        normalized = normalize_mesh_for_canonicalization(mesh)
        assert normalized["declared_invariants"] == sorted(mesh["declared_invariants"])

    def test_adjacency_pair_normalized(self):
        """Adjacency left must be <= right after normalization."""
        mesh = _minimal_tet()
        # Add two tetras and a shared adjacency that is "backwards"
        mesh["vertex_ids"] = ["v0", "v1", "v2", "v3", "v4"]
        mesh["tetrahedra"] = [
            {"tetra_id": "T0", "vertices": ["v0", "v1", "v2", "v3"]},
            {"tetra_id": "T1", "vertices": ["v0", "v2", "v1", "v4"]},
        ]
        # T1.face3 = (v0,v2,v1) shares with T0.face3 = (v0,v1,v2)
        mesh["adjacency"] = [
            # deliberately put T1 on the left
            {"left": {"tetra_id": "T1", "face": 3}, "right": {"tetra_id": "T0", "face": 3}}
        ]
        mesh["boundary_faces"] = [
            {"tetra_id": "T0", "face": 0},
            {"tetra_id": "T0", "face": 1},
            {"tetra_id": "T0", "face": 2},
            {"tetra_id": "T1", "face": 0},
            {"tetra_id": "T1", "face": 1},
            {"tetra_id": "T1", "face": 2},
        ]
        normalized = normalize_mesh_for_canonicalization(mesh)
        adj = normalized["adjacency"][0]
        left_key = (adj["left"]["tetra_id"], adj["left"]["face"])
        right_key = (adj["right"]["tetra_id"], adj["right"]["face"])
        assert left_key <= right_key


class TestTopologyProjection:
    """Unit tests for topology_projection()."""

    def test_excludes_geometry(self):
        mesh = _minimal_tet()
        mesh["geometry"] = {
            "coordinate_system": "euclidean_3d",
            "coordinates": {"v0": [0.0, 0.0, 0.0]},
        }
        proj = topology_projection(mesh)
        assert "geometry" not in proj

    def test_excludes_topology_hash(self):
        mesh = _minimal_tet()
        mesh["topology_hash"] = "sha256:" + "a" * 64
        proj = topology_projection(mesh)
        assert "topology_hash" not in proj

    def test_includes_required_fields(self):
        mesh = _minimal_tet()
        proj = topology_projection(mesh)
        for field in ("protocol", "version", "mesh_id", "vertex_ids", "tetrahedra",
                      "adjacency", "boundary_faces", "orientation_rule",
                      "canonicalization_version", "declared_invariants"):
            assert field in proj


class TestFacesOppositeOrientation:
    """Unit tests for faces_opposite_orientation()."""

    def test_reversed_face(self):
        # (v0,v1,v2) and (v2,v1,v0) are opposite
        assert faces_opposite_orientation(("v0", "v1", "v2"), ("v2", "v1", "v0"))

    def test_cyclic_rotation_of_reverse(self):
        # (v0,v1,v2) and (v1,v0,v2) — is this opposite?
        # Reverse of (v0,v1,v2) = (v2,v1,v0); cyclic rotations: (v2,v1,v0),(v1,v0,v2),(v0,v2,v1)
        assert faces_opposite_orientation(("v0", "v1", "v2"), ("v1", "v0", "v2"))
        assert faces_opposite_orientation(("v0", "v1", "v2"), ("v0", "v2", "v1"))

    def test_same_orientation(self):
        # (v0,v1,v2) and (v0,v1,v2) have the same orientation
        assert not faces_opposite_orientation(("v0", "v1", "v2"), ("v0", "v1", "v2"))

    def test_cyclic_rotation_same_orientation(self):
        # (v0,v1,v2) and (v1,v2,v0) — same cyclic orientation
        assert not faces_opposite_orientation(("v0", "v1", "v2"), ("v1", "v2", "v0"))


class TestGetFaceVertices:
    """Unit tests for get_face_vertices()."""

    def test_face_0(self):
        verts = ["v0", "v1", "v2", "v3"]
        assert get_face_vertices(verts, 0) == ("v1", "v2", "v3")

    def test_face_1(self):
        verts = ["v0", "v1", "v2", "v3"]
        assert get_face_vertices(verts, 1) == ("v0", "v2", "v3")

    def test_face_2(self):
        verts = ["v0", "v1", "v2", "v3"]
        assert get_face_vertices(verts, 2) == ("v0", "v1", "v3")

    def test_face_3(self):
        verts = ["v0", "v1", "v2", "v3"]
        assert get_face_vertices(verts, 3) == ("v0", "v1", "v2")


class TestLoadJson:
    """Unit tests for load_json()."""

    def test_valid_file(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write('{"key": "value"}')
            data, err = load_json(path)
            assert err is None
            assert data == {"key": "value"}
        finally:
            os.unlink(path)

    def test_missing_file(self):
        data, err = load_json("/nonexistent/path.json")
        assert data is None
        assert err is not None
        assert "not found" in err.lower() or "File" in err

    def test_invalid_json(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                f.write("{bad json")
            data, err = load_json(path)
            assert data is None
            assert err is not None
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Fail-closed behaviour
# ---------------------------------------------------------------------------

class TestFailClosed:
    """Verify fail-closed semantics: no silent PASS."""

    def test_missing_required_field_is_error_not_pass(self):
        mesh = _minimal_tet()
        del mesh["vertex_ids"]
        path = _write_tmp(mesh)
        try:
            verdict, exit_code, receipt = verify(path)
            assert verdict == "ERROR"
            assert exit_code != EXIT_PASS
        finally:
            os.unlink(path)

    def test_topology_hash_mismatch_is_fail(self):
        mesh = _minimal_tet()
        mesh["topology_hash"] = "sha256:" + "0" * 64
        path = _write_tmp(mesh)
        try:
            verdict, exit_code, receipt = verify(path)
            assert verdict == "FAIL"
            assert exit_code == EXIT_FAIL
        finally:
            os.unlink(path)

    def test_receipt_always_present_on_fail(self):
        verdict, exit_code, receipt = verify(_golden("fail_duplicate_tet.json"))
        assert "verdict" in receipt
        assert receipt["verdict"] == "FAIL"

    def test_receipt_always_present_on_error(self):
        verdict, exit_code, receipt = verify(_golden("error_malformed_schema.json"))
        assert "verdict" in receipt
        assert receipt["verdict"] == "ERROR"
