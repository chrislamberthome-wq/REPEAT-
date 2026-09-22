#!/usr/bin/env python3
"""
TMP Tetrahedral Mesh verifier CLI.

Usage:
    python -m cli.verify_tetra_mesh <mesh.json>

Exit codes:
    0 = PASS  — mesh verified successfully
    1 = FAIL  — mesh failed verification (orientation, volume, adjacency)
    2 = ERROR — runtime error (file not found, JSON parse error, etc.)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verifier.verify_mesh import verify_mesh  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(
            "usage: verify_tetra_mesh.py <mesh.json>",
            file=sys.stderr,
        )
        return 2

    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as f:
            mesh_state = json.load(f)
    except OSError as exc:
        print(f"ERROR: cannot open '{path}': {exc}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON parse error in '{path}': {exc}", file=sys.stderr)
        return 2

    try:
        receipt = verify_mesh(mesh_state)
    except Exception as exc:
        print(f"ERROR: verification error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(receipt, indent=2))

    result = receipt.get("result", "ERROR")
    if result == "PASS":
        return 0
    if result == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
