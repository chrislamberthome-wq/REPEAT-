#!/usr/bin/env python3
"""
CLI: Tetrahedral Mesh Verifier.

Usage:
    python cli/verify_tetra_mesh.py <mesh.json> [--print-hash]

Exit codes:
    0 = PASS
    1 = FAIL (invariant violation)
    2 = ERROR (malformed input / file not found)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running as script from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from verifier.tetra_mesh import compute_mesh_hash, verify_mesh


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a tetrahedral mesh JSON file per TMP v1.",
    )
    parser.add_argument(
        "mesh_json",
        help="Path to the mesh JSON file to verify.",
    )
    parser.add_argument(
        "--print-hash",
        action="store_true",
        help="Print the computed canonical hash to stdout (useful for CI debugging).",
    )
    args = parser.parse_args(argv)

    try:
        raw = Path(args.mesh_json).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read '{args.mesh_json}': {exc}", file=sys.stderr)
        return 2

    try:
        mesh = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON in '{args.mesh_json}': {exc}", file=sys.stderr)
        return 2

    if args.print_hash:
        try:
            h = compute_mesh_hash(mesh)
            print(f"canonical_hash: {h}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: hash computation failed: {exc}", file=sys.stderr)
            return 2

    receipt = verify_mesh(mesh)

    if receipt["result"] == "PASS":
        print(
            f"PASS: mesh '{receipt['mesh_id']}' verified "
            f"({receipt['cell_count']} cell(s)).",
        )
        return 0

    if receipt["result"] == "FAIL":
        print(
            f"FAIL: mesh '{receipt['mesh_id']}' failed verification.",
            file=sys.stderr,
        )
        for err in receipt.get("errors", []):
            print(f"  - {err}", file=sys.stderr)
        return 1

    # ERROR
    print(
        f"ERROR: mesh '{receipt['mesh_id']}': {receipt.get('errors', [])}",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
