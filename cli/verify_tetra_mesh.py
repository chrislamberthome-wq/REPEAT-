#!/usr/bin/env python3
"""
cli/verify_tetra_mesh.py

Command-line tool to verify a tetrahedral mesh state JSON file and
emit a verification receipt in JSON format.

Usage
-----
    python cli/verify_tetra_mesh.py mesh_state.json [--prev-hash <sha256>]
    python cli/verify_tetra_mesh.py mesh_state.json --output receipt.json

Exit codes
----------
  0  PASS
  1  FAIL
  2  ERROR (processing failure)
"""

import argparse
import json
import sys
import os

# Allow running as a standalone script from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from verifier.verify_mesh import verify_mesh  # noqa: E402


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Verify a tetrahedral mesh state JSON file (TMP v1).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "mesh_file",
        metavar="MESH_FILE",
        help="Path to the mesh state JSON file.",
    )
    parser.add_argument(
        "--prev-hash",
        default=None,
        metavar="SHA256",
        help="SHA-256 hex digest of the previous receipt (for chaining).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="RECEIPT_FILE",
        help="Write the receipt JSON to this file (default: stdout).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)

    # Load mesh state
    try:
        with open(args.mesh_file, "r", encoding="utf-8") as fh:
            mesh_state = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        error_receipt = {
            "receipt_type": "tetra_mesh_verification",
            "mesh_id": "<unknown>",
            "cell_count": 0,
            "timestamp": "",
            "canonical_hash": "0" * 64,
            "prev_receipt_hash": args.prev_hash,
            "verifier_version": "tmp_v1",
            "result": "ERROR",
            "failures": [f"Failed to load mesh file: {exc}"],
        }
        _emit(error_receipt, args.output)
        return 2

    receipt = verify_mesh(mesh_state, prev_receipt_hash=args.prev_hash)
    _emit(receipt, args.output)

    result_map = {"PASS": 0, "FAIL": 1, "ERROR": 2}
    return result_map.get(receipt.get("result", "ERROR"), 2)


def _emit(receipt, output_path):
    text = json.dumps(receipt, indent=2, ensure_ascii=False)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.write("\n")
    else:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
