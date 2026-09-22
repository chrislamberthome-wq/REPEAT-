"""
Tests for the Tetrahedral Mesh Protocol (TMP) final certification boundary.

Covers:
1. Frozen golden receipt shape — deterministic fields must not drift.
2. Negative canonicalization — semantically equivalent inputs → same bytes/hash.
3. CLI exit-code contract — 0=PASS, 1=FAIL, 2=ERROR.
4. Version-binding check — TMP_VERSION consistent across all touchpoints.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Shared test fixture
# ---------------------------------------------------------------------------

GOLDEN_MESH = {
    "mesh_id": "golden_tetra_001",
    "cells": [
        {
            "cell_id": "c0",
            "vertex_ids": ["v0", "v1", "v2", "v3"],
            "vertices": {
                "v0": [0.0, 0.0, 0.0],
                "v1": [1.0, 0.0, 0.0],
                "v2": [0.0, 1.0, 0.0],
                "v3": [0.0, 0.0, 1.0],
            },
            "orientation": "positive",
        }
    ],
}

# Frozen expected canonical hash for GOLDEN_MESH.
GOLDEN_CANONICAL_HASH = (
    "fcfb04a3751be5651b6057ebc180e190437789fedb760d3ae136436ebbffd0a6"
)

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. Frozen golden receipt shape
# ---------------------------------------------------------------------------


class TestGoldenReceiptShape:
    """The deterministic fields of the golden receipt must not drift."""

    def test_receipt_deterministic_fields(self):
        from verifier.verify_mesh import verify_mesh

        receipt = verify_mesh(GOLDEN_MESH)

        # Deterministic fields must be exactly these values.
        assert receipt["receipt_type"] == "tetra_mesh_verification"
        assert receipt["mesh_id"] == "golden_tetra_001"
        assert receipt["cell_count"] == 1
        assert receipt["canonical_hash"] == GOLDEN_CANONICAL_HASH
        assert receipt["verifier_version"] == "tmp_v1"
        assert receipt["result"] == "PASS"
        assert receipt["reasons"] == []

    def test_receipt_field_ordering(self):
        """The receipt must contain all required fields (no missing keys)."""
        from verifier.verify_mesh import verify_mesh

        receipt = verify_mesh(GOLDEN_MESH)
        required = {
            "receipt_type",
            "mesh_id",
            "cell_count",
            "canonical_hash",
            "verifier_version",
            "result",
            "reasons",
        }
        assert required.issubset(receipt.keys())

    def test_canonical_hash_frozen(self):
        """canonical_hash must equal the frozen golden value on every run."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        digest = hashlib.sha256(canonical_json_bytes(GOLDEN_MESH)).hexdigest()
        assert digest == GOLDEN_CANONICAL_HASH

    def test_replay_produces_pass(self):
        """Replaying the same mesh must always produce PASS."""
        from verifier.verify_mesh import verify_mesh

        for _ in range(3):
            receipt = verify_mesh(GOLDEN_MESH)
            assert receipt["result"] == "PASS"

    def test_tamper_produces_fail(self):
        """Modifying a vertex must flip the orientation and produce FAIL."""
        from verifier.verify_mesh import verify_mesh
        import copy

        tampered = copy.deepcopy(GOLDEN_MESH)
        # Flip v3 to create a negative-volume tetrahedron while keeping
        # orientation declared as "positive" → orientation mismatch → FAIL.
        tampered["cells"][0]["vertices"]["v3"] = [0.0, 0.0, -1.0]

        receipt = verify_mesh(tampered)
        assert receipt["result"] == "FAIL"
        assert len(receipt["reasons"]) > 0

    def test_tamper_changes_hash(self):
        """A tampered mesh must produce a different canonical_hash."""
        from verifier.canonicalize_mesh import canonical_json_bytes
        import copy

        tampered = copy.deepcopy(GOLDEN_MESH)
        tampered["cells"][0]["vertices"]["v3"] = [0.0, 0.0, -1.0]

        digest = hashlib.sha256(canonical_json_bytes(tampered)).hexdigest()
        assert digest != GOLDEN_CANONICAL_HASH


# ---------------------------------------------------------------------------
# 2. Negative canonicalization test
# ---------------------------------------------------------------------------


class TestNegativeCanonicalization:
    """Semantically identical inputs must produce identical canonical bytes."""

    def _make_mesh_variant_a(self):
        """Keys in 'natural' order, vertices in v0/v1/v2/v3 order."""
        return {
            "mesh_id": "canon_test",
            "cells": [
                {
                    "cell_id": "c0",
                    "vertex_ids": ["v0", "v1", "v2", "v3"],
                    "vertices": {
                        "v0": [0.0, 0.0, 0.0],
                        "v1": [1.0, 0.0, 0.0],
                        "v2": [0.0, 1.0, 0.0],
                        "v3": [0.0, 0.0, 1.0],
                    },
                    "orientation": "positive",
                }
            ],
        }

    def _make_mesh_variant_b(self):
        """Same mesh with keys in reversed order and vertex_ids shuffled."""
        return {
            "cells": [
                {
                    "orientation": "positive",
                    "vertices": {
                        "v3": [0.0, 0.0, 1.0],
                        "v2": [0.0, 1.0, 0.0],
                        "v1": [1.0, 0.0, 0.0],
                        "v0": [0.0, 0.0, 0.0],
                    },
                    "vertex_ids": ["v3", "v2", "v1", "v0"],
                    "cell_id": "c0",
                }
            ],
            "mesh_id": "canon_test",
        }

    def _make_mesh_variant_c(self):
        """Same mesh with floats written with trailing zeros or as integers."""
        return {
            "mesh_id": "canon_test",
            "cells": [
                {
                    "cell_id": "c0",
                    "vertex_ids": ["v0", "v1", "v2", "v3"],
                    "vertices": {
                        "v0": [0.0, 0.0, 0.0],
                        "v1": [1.000000000, 0.0, 0.0],
                        "v2": [0.0, 1.000000000, 0.0],
                        "v3": [0.0, 0.0, 1.000000000],
                    },
                    "orientation": "positive",
                }
            ],
        }

    def test_key_order_variants_same_bytes(self):
        """Different key orderings must yield identical canonical bytes."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        a = canonical_json_bytes(self._make_mesh_variant_a())
        b = canonical_json_bytes(self._make_mesh_variant_b())
        assert a == b

    def test_vertex_order_variants_same_bytes(self):
        """Different vertex_ids orderings must yield identical canonical bytes."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        a = canonical_json_bytes(self._make_mesh_variant_a())
        b = canonical_json_bytes(self._make_mesh_variant_b())
        assert a == b

    def test_float_representation_variants_same_bytes(self):
        """Equivalent float values must yield identical canonical bytes."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        a = canonical_json_bytes(self._make_mesh_variant_a())
        c = canonical_json_bytes(self._make_mesh_variant_c())
        assert a == c

    def test_all_variants_same_hash(self):
        """All three variants must produce the same SHA-256 hash."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        def h(mesh):
            return hashlib.sha256(canonical_json_bytes(mesh)).hexdigest()

        ha = h(self._make_mesh_variant_a())
        hb = h(self._make_mesh_variant_b())
        hc = h(self._make_mesh_variant_c())
        assert ha == hb == hc

    def test_canonical_bytes_are_deterministic_on_repeated_calls(self):
        """canonical_json_bytes must return the same bytes on every call."""
        from verifier.canonicalize_mesh import canonical_json_bytes

        mesh = self._make_mesh_variant_a()
        results = {canonical_json_bytes(mesh) for _ in range(5)}
        assert len(results) == 1


# ---------------------------------------------------------------------------
# 3. CLI exit-code contract
# ---------------------------------------------------------------------------


class TestCLIExitCodeContract:
    """
    Exit-code contract:
        0 = PASS  — mesh verified OK
        1 = FAIL  — mesh failed verification
        2 = ERROR — runtime error
    """

    @staticmethod
    def _run_cli(mesh_json: str) -> int:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write(mesh_json)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "cli" / "verify_tetra_mesh.py"), tmp_path],
                capture_output=True,
            )
            return result.returncode
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_exit_0_on_pass(self):
        """Valid mesh → exit code 0 (PASS)."""
        code = self._run_cli(json.dumps(GOLDEN_MESH))
        assert code == 0, f"Expected exit code 0, got {code}"

    def test_exit_1_on_fail(self):
        """Mesh with orientation mismatch → exit code 1 (FAIL)."""
        import copy

        bad_mesh = copy.deepcopy(GOLDEN_MESH)
        # Flip vertex to produce a negative-volume cell but keep orientation=positive
        bad_mesh["cells"][0]["vertices"]["v3"] = [0.0, 0.0, -1.0]
        code = self._run_cli(json.dumps(bad_mesh))
        assert code == 1, f"Expected exit code 1, got {code}"

    def test_exit_2_on_missing_file(self):
        """Non-existent file → exit code 2 (ERROR)."""
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "cli" / "verify_tetra_mesh.py"),
                str(Path(tempfile.gettempdir()) / "__nonexistent_tmp_mesh__.json"),
            ],
            capture_output=True,
        )
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"

    def test_exit_2_on_invalid_json(self):
        """File containing invalid JSON → exit code 2 (ERROR)."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("{ not valid json }")
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, str(REPO_ROOT / "cli" / "verify_tetra_mesh.py"), tmp_path],
                capture_output=True,
            )
            assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_exit_2_on_no_args(self):
        """No arguments → exit code 2 (ERROR)."""
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "cli" / "verify_tetra_mesh.py")],
            capture_output=True,
        )
        assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"


# ---------------------------------------------------------------------------
# 4. Version-binding check
# ---------------------------------------------------------------------------


class TestVersionBinding:
    """TMP_VERSION must be consistent across all touchpoints."""

    def test_tmp_metadata_exports_version(self):
        from verifier.tmp_metadata import TMP_VERSION

        assert TMP_VERSION == "tmp_v1"

    def test_verifier_version_matches_tmp_version(self):
        from verifier.tmp_metadata import TMP_VERSION
        from verifier.verify_mesh import VERIFIER_VERSION

        assert VERIFIER_VERSION == TMP_VERSION, (
            f"VERIFIER_VERSION ({VERIFIER_VERSION!r}) != TMP_VERSION ({TMP_VERSION!r})"
        )

    def test_receipt_verifier_version_matches_tmp_version(self):
        """The emitted receipt must carry the canonical TMP_VERSION string."""
        from verifier.tmp_metadata import TMP_VERSION
        from verifier.verify_mesh import verify_mesh

        receipt = verify_mesh(GOLDEN_MESH)
        assert receipt["verifier_version"] == TMP_VERSION, (
            f"receipt.verifier_version ({receipt['verifier_version']!r}) "
            f"!= TMP_VERSION ({TMP_VERSION!r})"
        )

    def test_docs_reference_correct_version(self):
        """The protocol documentation must reference the current TMP version."""
        from verifier.tmp_metadata import TMP_VERSION

        doc_path = REPO_ROOT / "docs" / "TETRAHEDRAL_MESH_PROTOCOL_v1.md"
        assert doc_path.exists(), f"Documentation file not found: {doc_path}"
        content = doc_path.read_text(encoding="utf-8")
        assert TMP_VERSION in content, (
            f"TMP_VERSION ({TMP_VERSION!r}) not found in {doc_path}"
        )

    def test_all_version_touchpoints_consistent(self):
        """All version touchpoints must agree on the same string."""
        from verifier.tmp_metadata import TMP_VERSION
        from verifier.verify_mesh import VERIFIER_VERSION
        from verifier.verify_mesh import verify_mesh

        receipt = verify_mesh(GOLDEN_MESH)
        receipt_version = receipt["verifier_version"]

        doc_path = REPO_ROOT / "docs" / "TETRAHEDRAL_MESH_PROTOCOL_v1.md"
        doc_contains_version = TMP_VERSION in doc_path.read_text(encoding="utf-8")

        assert TMP_VERSION == VERIFIER_VERSION == receipt_version, (
            f"Version mismatch: TMP_VERSION={TMP_VERSION!r}, "
            f"VERIFIER_VERSION={VERIFIER_VERSION!r}, "
            f"receipt.verifier_version={receipt_version!r}"
        )
        assert doc_contains_version, (
            f"Documentation does not reference TMP_VERSION={TMP_VERSION!r}"
        )
