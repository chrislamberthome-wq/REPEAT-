"""
Replay tests for the Tetrahedral Mesh Verifier.

Ensures that replaying the verification of the golden mesh produces a
canonical hash that is stable and matches the frozen digest.

This simulates cross-environment determinism: if a stored receipt hash
can be reproduced from the same input on a different machine/OS/Python
version, canonicalization is working correctly.
"""
from __future__ import annotations

import copy
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


class TestReplayGoldenVector:
    """Replaying verification must produce the same canonical hash each time."""

    def test_hash_is_deterministic_across_calls(self, golden_mesh):
        """Same input must produce the same hash on repeated calls."""
        h1 = compute_mesh_hash(golden_mesh)
        h2 = compute_mesh_hash(golden_mesh)
        assert h1 == h2, "Hash is non-deterministic: two calls returned different values"

    def test_replay_hash_matches_frozen_digest(self, golden_mesh, frozen_digest):
        """Replayed hash must equal the frozen digest."""
        replayed = compute_mesh_hash(golden_mesh)
        assert replayed == frozen_digest, (
            f"Replay mismatch!\n"
            f"  frozen  : {frozen_digest}\n"
            f"  replayed: {replayed}"
        )

    def test_verify_result_stable_across_replays(self, golden_mesh):
        """Multiple verify_mesh calls must all return PASS."""
        for run in range(3):
            receipt = verify_mesh(golden_mesh)
            assert receipt["result"] == "PASS", (
                f"Run {run + 1}: expected PASS, got {receipt['result']}. "
                f"Errors: {receipt.get('errors', [])}"
            )

    def test_canonical_hash_stable_in_receipt(self, golden_mesh, frozen_digest):
        """The canonical_hash inside the receipt must match the frozen digest."""
        receipt1 = verify_mesh(golden_mesh)
        receipt2 = verify_mesh(golden_mesh)
        assert receipt1["canonical_hash"] == receipt2["canonical_hash"], (
            "canonical_hash differs between two verify_mesh calls"
        )
        assert receipt1["canonical_hash"] == frozen_digest

    def test_mutation_changes_hash(self, golden_mesh):
        """Mutating a vertex coordinate must produce a different hash."""
        original_hash = compute_mesh_hash(golden_mesh)

        # Deep-copy to avoid polluting the fixture
        mutated = copy.deepcopy(golden_mesh)
        mutated["cells"][0]["vertices"]["v2"][0] = 2.0  # change x of v2

        mutated_hash = compute_mesh_hash(mutated)
        assert mutated_hash != original_hash, (
            "Mutating a vertex coordinate should change the canonical hash"
        )

    def test_mutation_causes_fail_in_verify(self, golden_mesh):
        """Mutating a vertex to make the cell degenerate must yield FAIL."""
        degenerate = copy.deepcopy(golden_mesh)
        # Move v4 onto the plane of v1, v2, v3
        degenerate["cells"][0]["vertices"]["v4"] = [1, 1, 0]

        receipt = verify_mesh(degenerate)
        assert receipt["result"] == "FAIL", (
            f"Expected FAIL for degenerate mesh but got {receipt['result']}"
        )
