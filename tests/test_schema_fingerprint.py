from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"
EXPECTED_SHA256 = "425d424acd2e44711a9f7de5c958a45788b22b1edb7e5eb3de9e5f3a355e6f94"

def test_repo_reference_schema_fingerprint() -> None:
    actual_sha256 = hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    assert actual_sha256 == EXPECTED_SHA256, (
        f"schema fingerprint drift detected for {SCHEMA_PATH}: "
        f"expected {EXPECTED_SHA256}, got {actual_sha256}"
    )
