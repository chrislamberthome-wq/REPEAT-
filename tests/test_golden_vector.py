"""
Golden vector tests for the Tetrahedral Mesh Verifier.

Validates that:
1. The canonical hash of the golden vector matches the frozen digest.
2. The golden vector passes all invariant checks (result == PASS).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from verifier.tetra_mesh import compute_mesh_hash, verify_mesh

VECTORS_DIR = Path(__file__).parent / "vectors"
GOLDEN_JSON = VECTORS_DIR / "golden_tetra_mesh.json"
GOLDEN_SHA256 = VECTORS_DIR / "golden_tetra_mesh.sha256"


@pytest.fixture(scope="module")
def golden_mesh() -> dict:
    return json.loads(GOLDEN_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def frozen_digest() -> str:
    return GOLDEN_SHA256.read_text(encoding="utf-8").strip()


class TestGoldenVectorDigest:
    """Hash of the golden vector must match the frozen digest."""

    def test_frozen_digest_file_exists(self):
        assert GOLDEN_SHA256.exists(), f"Missing frozen digest: {GOLDEN_SHA256}"

    def test_golden_json_file_exists(self):
        assert GOLDEN_JSON.exists(), f"Missing golden vector: {GOLDEN_JSON}"

    def test_hash_matches_frozen_digest(self, golden_mesh, frozen_digest):
        computed = compute_mesh_hash(golden_mesh)
        assert computed == frozen_digest, (
            f"Hash mismatch!\n"
            f"  frozen : {frozen_digest}\n"
            f"  computed: {computed}\n"
            "Run scripts/freeze_golden_vector.py to refresh the digest "
            "if this is an intentional change."
        )

    def test_frozen_digest_format(self, frozen_digest):
        assert frozen_digest.startswith("sha256:"), (
            f"Digest must start with 'sha256:' prefix, got: {frozen_digest!r}"
        )
        hex_part = frozen_digest[len("sha256:"):]
        assert len(hex_part) == 64, (
            f"Expected 64 hex chars after prefix, got {len(hex_part)}"
        )
        assert all(c in "0123456789abcdef" for c in hex_part), (
            f"Non-hex character in digest: {frozen_digest!r}"
        )


class TestGoldenVectorVerification:
    """The golden vector must verify successfully (PASS)."""

    def test_verify_result_is_pass(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert receipt["result"] == "PASS", (
            f"Expected PASS but got {receipt['result']}.\n"
            f"Errors: {receipt.get('errors', [])}"
        )

    def test_receipt_has_canonical_hash(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert "canonical_hash" in receipt
        assert receipt["canonical_hash"].startswith("sha256:")

    def test_receipt_canonical_hash_matches_frozen_digest(self, golden_mesh, frozen_digest):
        receipt = verify_mesh(golden_mesh)
        assert receipt["canonical_hash"] == frozen_digest, (
            f"Receipt hash does not match frozen digest.\n"
            f"  frozen  : {frozen_digest}\n"
            f"  receipt : {receipt['canonical_hash']}"
        )

    def test_receipt_cell_count(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert receipt["cell_count"] == len(golden_mesh["cells"])

    def test_receipt_mesh_id(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert receipt["mesh_id"] == golden_mesh["mesh_id"]

    def test_receipt_verifier_version(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert receipt["verifier_version"] == "tmp_v1"

    def test_no_errors_in_receipt(self, golden_mesh):
        receipt = verify_mesh(golden_mesh)
        assert receipt["errors"] == [], (
            f"Unexpected errors: {receipt['errors']}"
        )
