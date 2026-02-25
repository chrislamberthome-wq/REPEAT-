#!/usr/bin/env python3
"""
REPEAT receipt verifier — canonical entrypoint.

Usage:
    python -m verifier <receipts.jsonl>

Exit codes:
    0 = all receipts valid
    1 = validation failure (schema violation, hash mismatch, or failed verdict)
    2 = runtime error (file not found, JSON parse error, etc.)

Validates:
    - Required fields present (per repeat-spintronics-receipt-v1 schema)
    - evidence_hash_sha256 recomputed and matches stored value
    - receipt_hash_sha256 recomputed and matches stored value
    - No receipt has verdict.pass == false (fail-closed)

Cross-receipt hash chain: NOT validated — chain is absent in this repo.
Absence is documented in docs/autotonomy/IMPLEMENTATION_MAP.md, not invented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Tuple


REQUIRED_FIELDS = [
    "schema",
    "packet_hash_sha256",
    "evidence_hash_sha256",
    "receipt_hash_sha256",
    "run_id",
    "measured_resistance_ohms",
    "verdict",
    "metrics",
]

EXPECTED_SCHEMA = "repeat-spintronics-receipt-v1"
SHA256_PREFIX = "sha256:"


def canonical_json(obj: Dict[str, Any]) -> bytes:
    """Canonical JSON per REPEAT C14N v1 (JCS / RFC 8785)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def sha256_c14n(obj: Dict[str, Any]) -> str:
    """Compute sha256 of canonical JSON."""
    digest = hashlib.sha256(canonical_json(obj)).hexdigest()
    return SHA256_PREFIX + digest


def validate_hash_format(value: str, field: str) -> List[str]:
    """Validate that a hash field has the expected format."""
    errors = []
    if not isinstance(value, str):
        errors.append(f"{field}: expected string, got {type(value).__name__}")
        return errors
    if not value.startswith(SHA256_PREFIX):
        errors.append(f"{field}: missing 'sha256:' prefix")
    elif len(value) != len(SHA256_PREFIX) + 64:
        errors.append(f"{field}: expected 64 hex chars after prefix, got {len(value) - len(SHA256_PREFIX)}")
    return errors


def validate_receipt(receipt: Dict[str, Any], index: int) -> List[str]:
    """
    Validate a single receipt. Returns a list of error strings (empty = valid).
    """
    errors = []
    label = f"receipt[{index}] run_id={receipt.get('run_id', '?')}"

    # 1. Required fields
    for field in REQUIRED_FIELDS:
        if field not in receipt:
            errors.append(f"{label}: missing required field '{field}'")

    if errors:
        return errors  # can't validate further without required fields

    # 2. Schema string
    if receipt["schema"] != EXPECTED_SCHEMA:
        errors.append(
            f"{label}: schema mismatch: expected '{EXPECTED_SCHEMA}', "
            f"got '{receipt['schema']}'"
        )

    # 3. Hash format validation
    for hash_field in ("packet_hash_sha256", "evidence_hash_sha256", "receipt_hash_sha256"):
        errors.extend(validate_hash_format(receipt[hash_field], f"{label}.{hash_field}"))

    # 4. Recompute evidence_hash_sha256
    # evidence_hash is computed over receipt minus evidence_hash and receipt_hash fields
    receipt_for_evidence = {
        k: v for k, v in receipt.items()
        if k not in ("evidence_hash_sha256", "receipt_hash_sha256")
    }
    expected_evidence_hash = sha256_c14n(receipt_for_evidence)
    if receipt["evidence_hash_sha256"] != expected_evidence_hash:
        errors.append(
            f"{label}: evidence_hash_sha256 mismatch: "
            f"stored={receipt['evidence_hash_sha256']}, "
            f"computed={expected_evidence_hash}"
        )

    # 5. Recompute receipt_hash_sha256
    # receipt_hash is computed over receipt minus receipt_hash field
    receipt_for_hash = {
        k: v for k, v in receipt.items()
        if k != "receipt_hash_sha256"
    }
    expected_receipt_hash = sha256_c14n(receipt_for_hash)
    if receipt["receipt_hash_sha256"] != expected_receipt_hash:
        errors.append(
            f"{label}: receipt_hash_sha256 mismatch: "
            f"stored={receipt['receipt_hash_sha256']}, "
            f"computed={expected_receipt_hash}"
        )

    # 6. Verdict field
    verdict = receipt["verdict"]
    if not isinstance(verdict, dict):
        errors.append(f"{label}: verdict must be an object")
    elif "pass" not in verdict:
        errors.append(f"{label}: verdict missing 'pass' field")
    elif verdict["pass"] is False:
        reason = verdict.get("fail_reason", "unspecified")
        errors.append(f"{label}: verdict FAIL (fail_reason={reason})")

    return errors


def _is_verdict_failure(error: str) -> bool:
    """Return True if an error string represents a verdict FAIL (not a structural error)."""
    return ": verdict FAIL " in error


def load_receipts(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Load receipts from a JSONL file.
    Returns (receipts, parse_errors).
    """
    receipts = []
    parse_errors = []
    try:
        with open(path, 'r') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    receipts.append(json.loads(line))
                except json.JSONDecodeError as e:
                    parse_errors.append(f"line {lineno}: JSON parse error: {e}")
    except OSError as e:
        raise RuntimeError(f"Cannot open '{path}': {e}") from e
    return receipts, parse_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="REPEAT receipt verifier — validates JSONL receipts fail-closed."
    )
    parser.add_argument(
        "receipts",
        help="Path to JSONL receipts file (one receipt per line)",
    )
    parser.add_argument(
        "--allow-fail-verdicts",
        action="store_true",
        help="Do not treat verdict.pass==false as a validation error "
             "(useful when auditing known-failure runs).",
    )
    args = parser.parse_args()

    try:
        receipts, parse_errors = load_receipts(args.receipts)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    all_errors = []

    if parse_errors:
        all_errors.extend(parse_errors)

    if not receipts and not parse_errors:
        print("WARNING: no receipts found in file", file=sys.stderr)

    for i, receipt in enumerate(receipts):
        receipt_errors = validate_receipt(receipt, i)
        if args.allow_fail_verdicts:
            receipt_errors = [
                e for e in receipt_errors
                if not _is_verdict_failure(e)
            ]
        all_errors.extend(receipt_errors)

    if all_errors:
        for err in all_errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(
            f"\nVerification FAILED: {len(all_errors)} error(s) in "
            f"{len(receipts)} receipt(s).",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {len(receipts)} receipt(s) verified successfully.",
        file=sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
