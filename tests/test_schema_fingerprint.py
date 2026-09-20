from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"
EXPECTED_SHA256 = "bdba59782604f14962fb85b35ea2acf70df8968fa1210f38360e9e1dbe1edceb"


def test_repo_reference_schema_fingerprint() -> None:
    actual_sha256 = hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
    assert actual_sha256 == EXPECTED_SHA256, (
        f"schema fingerprint drift detected for {SCHEMA_PATH}: "
        f"expected {EXPECTED_SHA256}, got {actual_sha256}"
    )
