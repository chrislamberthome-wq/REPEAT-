#!/usr/bin/env python3
"""
freeze_golden_vector.py — Refresh the frozen SHA-256 digest for the golden
tetrahedral mesh vector.

Usage:
    python scripts/freeze_golden_vector.py

This script recomputes the canonical hash of tests/vectors/golden_tetra_mesh.json
and writes it to tests/vectors/golden_tetra_mesh.sha256.

Use this only for deliberate, controlled updates to the golden vector.
Do NOT run this automatically in CI; the frozen digest is the source of truth.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running from any working directory
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from verifier.tetra_mesh import compute_mesh_hash

GOLDEN_JSON = REPO_ROOT / "tests" / "vectors" / "golden_tetra_mesh.json"
GOLDEN_SHA256 = REPO_ROOT / "tests" / "vectors" / "golden_tetra_mesh.sha256"


def main() -> int:
    if not GOLDEN_JSON.exists():
        print(f"ERROR: golden vector not found: {GOLDEN_JSON}", file=sys.stderr)
        return 1

    mesh = json.loads(GOLDEN_JSON.read_text(encoding="utf-8"))
    digest = compute_mesh_hash(mesh)

    existing = GOLDEN_SHA256.read_text(encoding="utf-8").strip() if GOLDEN_SHA256.exists() else None

    if existing == digest:
        print(f"Digest unchanged: {digest}")
        print(f"File: {GOLDEN_SHA256}")
        return 0

    GOLDEN_SHA256.write_text(digest + "\n", encoding="utf-8")

    if existing:
        print(f"Digest updated:")
        print(f"  old: {existing}")
        print(f"  new: {digest}")
    else:
        print(f"Digest created: {digest}")
    print(f"File: {GOLDEN_SHA256}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
