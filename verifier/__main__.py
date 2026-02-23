#!/usr/bin/env python3
"""
Canonical verifier entrypoint for REPEAT- receipts.

Usage:
    python -m verifier <receipts.jsonl>
    python -m verifier --schema schemas/repeat-spintronics-receipt-v1.schema.json <receipts.jsonl>

Exit codes:
    0 = PASS  — all receipts validated
    1 = FAIL  — one or more receipts failed validation
    2 = ERROR — runtime / file / schema error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------------------------------
# Required top-level fields (subset from receipt schema v1)
# ---------------------------------------------------------------------------
REQUIRED_FIELDS = {
    "schema",
    "packet_hash_sha256",
    "evidence_hash_sha256",
    "receipt_hash_sha256",
    "run_id",
    "verdict",
}

HASH_PREFIX = "sha256:"
HASH_STR_LEN = len(HASH_PREFIX) + 64  # "sha256:" + 64 hex chars
_HEX_CHARS = set("0123456789abcdef")


def _sha256_c14n(obj: Dict[str, Any]) -> str:
    """
    Compute sha256 over the canonical (sorted-key) JSON representation of obj.
    Matches the C14N_RULES.md algorithm (JCS / RFC 8785 approximation).
    """
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return HASH_PREFIX + digest


def _is_valid_hash(value: Any) -> bool:
    """Return True if value looks like a well-formed sha256 hash string."""
    return (
        isinstance(value, str)
        and value.startswith(HASH_PREFIX)
        and len(value) == HASH_STR_LEN
        and all(c in _HEX_CHARS for c in value[len(HASH_PREFIX):])
    )


def validate_receipt(receipt: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single receipt object.  Returns a list of error strings (empty = PASS).
    """
    errors: List[str] = []
    tag = f"receipt[{index}]"

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in receipt:
            errors.append(f"{tag}: missing required field '{field}'")

    if errors:
        return errors  # can't proceed without required fields

    # 2. Hash format checks
    for hash_field in ("packet_hash_sha256", "evidence_hash_sha256", "receipt_hash_sha256"):
        if not _is_valid_hash(receipt.get(hash_field)):
            errors.append(f"{tag}: '{hash_field}' is not a valid sha256 hash string")

    # 3. verdict structure
    verdict = receipt.get("verdict", {})
    if not isinstance(verdict, dict) or "pass" not in verdict:
        errors.append(f"{tag}: 'verdict' must be an object with a 'pass' boolean field")

    # 4. receipt_hash_sha256 integrity check
    # Recompute receipt hash over the receipt without receipt_hash_sha256
    if _is_valid_hash(receipt.get("receipt_hash_sha256")):
        obj_without_receipt_hash = {k: v for k, v in receipt.items()
                                    if k != "receipt_hash_sha256"}
        expected = _sha256_c14n(obj_without_receipt_hash)
        if expected != receipt["receipt_hash_sha256"]:
            errors.append(
                f"{tag}: receipt_hash_sha256 mismatch — "
                f"stored={receipt['receipt_hash_sha256']}, computed={expected}"
            )

    return errors


def verify_file(jsonl_path: str) -> Tuple[int, int, List[str]]:
    """
    Verify all receipts in a JSONL file.

    Returns:
        (pass_count, fail_count, all_errors)
    """
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {jsonl_path}")

    all_errors: List[str] = []
    pass_count = 0
    fail_count = 0

    with path.open("r", encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                all_errors.append(f"line {lineno}: JSON parse error — {exc}")
                fail_count += 1
                continue

            errors = validate_receipt(obj, lineno)
            if errors:
                all_errors.extend(errors)
                fail_count += 1
            else:
                pass_count += 1

    return pass_count, fail_count, all_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m verifier",
        description="Validate REPEAT receipt JSONL files (fail-closed).",
    )
    parser.add_argument(
        "receipts",
        nargs="+",
        help="One or more JSONL receipt files to validate",
    )
    args = parser.parse_args()

    total_pass = 0
    total_fail = 0

    for receipts_file in args.receipts:
        try:
            passes, fails, errors = verify_file(receipts_file)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"ERROR: unexpected error reading {receipts_file}: {exc}", file=sys.stderr)
            return 2

        total_pass += passes
        total_fail += fails

        if errors:
            print(f"FAIL: {receipts_file}", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
        else:
            print(f"PASS: {receipts_file} ({passes} receipts validated)", file=sys.stderr)

    if total_fail > 0:
        print(
            f"\nVerification FAILED: {total_fail} invalid, {total_pass} valid",
            file=sys.stderr,
        )
        return 1

    print(f"\nVerification PASSED: {total_pass} receipts validated", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
