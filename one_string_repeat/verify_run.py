"""
verify_run.py — CLI for one_string_REPEAT v1.0 certifying loop.

Usage:
    python -m one_string_repeat.verify_run <payload.json>
    python -m one_string_repeat.verify_run --json <payload.json>

Exit codes:
    0  PASS   — run verified successfully
    1  FAIL   — replay produced a different result from the claimed receipt
    2  ERROR  — malformed input, engine exception, or verification incomplete

Certifying loop:
    1. Read and parse payload JSON.
    2. Canonicalize to bytes.
    3. Compute SHA-256 and CRC-16/CCITT-FALSE.
    4. Execute engine → run_receipt.
    5. Replay from canonical bytes → compare → verification_receipt.
    6. Print receipts and exit with appropriate code.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .canonical import canonicalize_string
from .crc16 import crc16_hex
from .hashutil import sha256_hex
from .receipt import generate as generate_receipt
from .verifier import verify


def _load_payload(path: str) -> dict[str, Any]:
    """Read and parse a JSON payload file. Raises SystemExit on error."""
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {path!r}: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        # canonicalize_string also checks for duplicate keys
        payload_bytes = canonicalize_string(raw)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    # Re-parse from canonical bytes for use as a Python dict
    payload = json.loads(payload_bytes.decode("utf-8"))
    return payload  # type: ignore[return-value]


def certify(payload: dict[str, Any], *, verbose: bool = True, as_json: bool = False) -> int:
    """
    Run the full certifying loop for *payload*.

    Returns an exit code: 0=PASS, 1=FAIL, 2=ERROR.
    """
    # Canonicalize + digest
    try:
        payload_bytes = canonicalize_string(json.dumps(payload))
    except ValueError as exc:
        if verbose:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    p_sha256 = sha256_hex(payload_bytes)
    p_crc16 = crc16_hex(payload_bytes)

    if verbose and not as_json:
        print(f"payload SHA-256  : {p_sha256}")
        print(f"payload CRC-16   : {p_crc16}")
        print()

    # Generate run_receipt
    run_receipt = generate_receipt(payload)

    # Verify
    vr = verify(payload, run_receipt)

    if as_json:
        out = {
            "payload_sha256": p_sha256,
            "payload_crc16_ccitt_false": p_crc16,
            "run_receipt": run_receipt,
            "verification_receipt": vr,
        }
        print(json.dumps(out, indent=2))
    elif verbose:
        print("=== run_receipt ===")
        print(json.dumps(run_receipt, indent=2))
        print()
        print("=== verification_receipt ===")
        print(json.dumps(vr, indent=2))
        print()
        result = vr["verification_result"]
        print(f"RESULT: {result}")

    code_map = {"PASS": 0, "FAIL": 1, "ERROR": 2}
    return code_map.get(vr.get("verification_result", "ERROR"), 2)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="verify_run",
        description="one_string_REPEAT v1.0 — certifying loop CLI",
    )
    parser.add_argument(
        "payload",
        help="Path to a one_string_payload JSON file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit all receipts as a single JSON object instead of human-readable output",
    )
    args = parser.parse_args()

    payload = _load_payload(args.payload)
    return certify(payload, verbose=True, as_json=args.as_json)


if __name__ == "__main__":
    sys.exit(main())
