#!/usr/bin/env python3
"""
REPEAT Council Action Verifier (repeat_verifier.py).

Deterministic verifier for council governance actions. Emits PASS, FAIL, or ERROR
to stdout and exits with the corresponding exit code.

Exit codes:
  0 = PASS — action is valid
  1 = FAIL — action is structurally invalid or violates governance rules
  2 = ERROR — infrastructure fault (file not found, JSON parse error, etc.)

This verifier is the SOLE authority for action validation outcomes.
OpenCode or other advisory tools must never reinterpret or override its output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Tuple

SCHEMA_VERSION = "c9-action-v1.0"
COUNCIL_ID = "council_of_9"
SEAT_RANGE = range(1, 10)  # 1..9 inclusive
SHA256_PREFIX = "sha256:"
QUORUM_THRESHOLD = 5  # default; may be overridden by council state

REQUIRED_ACTION_FIELDS = [
    "schema_version",
    "action_type",
    "council_id",
    "target_seat_id",
    "candidate",
    "proposed_at_utc",
    "proposer_public_key",
    "action_hash_sha256",
]

VALID_ACTION_TYPES = {"seat_fill", "seat_vacate", "seat_revoke"}

REQUIRED_CANDIDATE_FIELDS = ["public_key", "identity_hash_sha256"]


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
    """Compute SHA-256 of canonical JSON, prefixed with 'sha256:'."""
    digest = hashlib.sha256(canonical_json(obj)).hexdigest()
    return SHA256_PREFIX + digest


def validate_hash_format(value: Any, field: str) -> List[str]:
    """Validate that a hash field has the correct sha256:<64hex> format."""
    errors: List[str] = []
    if not isinstance(value, str):
        errors.append(f"{field}: expected string, got {type(value).__name__}")
        return errors
    if not value.startswith(SHA256_PREFIX):
        errors.append(f"{field}: missing 'sha256:' prefix")
    elif len(value) != len(SHA256_PREFIX) + 64:
        errors.append(
            f"{field}: expected 64 hex chars after prefix, "
            f"got {len(value) - len(SHA256_PREFIX)}"
        )
    return errors


def verify_action(action: Dict[str, Any]) -> Tuple[str, str, List[str]]:
    """
    Verify a governance action.

    Returns (result, reason, errors) where result is 'PASS', 'FAIL', or 'ERROR'
    and reason is a machine-readable code.
    """
    errors: List[str] = []

    # 1. Required fields
    for field in REQUIRED_ACTION_FIELDS:
        if field not in action:
            errors.append(f"missing required field '{field}'")

    if errors:
        return "FAIL", "missing_required_fields", errors

    # 2. Schema version
    if action["schema_version"] != SCHEMA_VERSION:
        errors.append(
            f"schema_version mismatch: expected '{SCHEMA_VERSION}', "
            f"got '{action['schema_version']}'"
        )

    # 3. Action type
    if action["action_type"] not in VALID_ACTION_TYPES:
        errors.append(
            f"action_type '{action['action_type']}' not in {sorted(VALID_ACTION_TYPES)}"
        )

    # 4. Council ID
    if action["council_id"] != COUNCIL_ID:
        errors.append(
            f"council_id mismatch: expected '{COUNCIL_ID}', "
            f"got '{action['council_id']}'"
        )

    # 5. Seat ID range
    seat_id = action["target_seat_id"]
    if not isinstance(seat_id, int) or seat_id not in SEAT_RANGE:
        errors.append(
            f"target_seat_id must be integer in 1..9, got {seat_id!r}"
        )

    # 6. Candidate fields
    candidate = action.get("candidate", {})
    if not isinstance(candidate, dict):
        errors.append("candidate must be an object")
    else:
        for cf in REQUIRED_CANDIDATE_FIELDS:
            if cf not in candidate:
                errors.append(f"candidate.{cf}: missing required field")
        if "identity_hash_sha256" in candidate:
            errors.extend(
                validate_hash_format(
                    candidate["identity_hash_sha256"],
                    "candidate.identity_hash_sha256",
                )
            )

    # 7. Action hash integrity — recompute and compare
    action_for_hash = {
        k: v for k, v in action.items() if k != "action_hash_sha256"
    }
    expected_hash = sha256_c14n(action_for_hash)
    stored_hash = action.get("action_hash_sha256", "")
    hash_format_errors = validate_hash_format(stored_hash, "action_hash_sha256")
    if hash_format_errors:
        errors.extend(hash_format_errors)
    elif stored_hash != expected_hash:
        errors.append(
            f"action_hash_sha256 mismatch: "
            f"stored={stored_hash}, computed={expected_hash}"
        )

    if errors:
        # Distinguish signature/hash errors from other failures
        if any("mismatch" in e and "action_hash_sha256" in e for e in errors):
            return "FAIL", "bad_signature", errors
        return "FAIL", "schema_violation", errors

    return "PASS", "action_valid", []


def load_action(path: str) -> Dict[str, Any]:
    """Load a JSON action file. Raises RuntimeError on I/O or parse error."""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except OSError as e:
        raise RuntimeError(f"Cannot open '{path}': {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error in '{path}': {e}") from e


def verify_receipt(receipt: Dict[str, Any]) -> Tuple[str, str, List[str]]:
    """
    Verify a seat_fill receipt structure.

    Returns (result, reason, errors).
    """
    errors: List[str] = []
    required = [
        "receipt_type", "spec_version", "ledger_seq", "action",
        "target_seat_id", "council_id", "entry_sha256",
        "prev_state_sha256", "next_state_sha256",
        "result", "reason", "verified_at_utc", "verifier", "verifier_signature",
    ]
    for field in required:
        if field not in receipt:
            errors.append(f"missing required field '{field}'")

    if errors:
        return "FAIL", "missing_required_fields", errors

    if receipt["receipt_type"] != "seat_fill_receipt":
        errors.append(
            f"receipt_type mismatch: expected 'seat_fill_receipt', "
            f"got '{receipt['receipt_type']}'"
        )
    if receipt["spec_version"] != "c9-receipt-v1.0":
        errors.append(
            f"spec_version mismatch: expected 'c9-receipt-v1.0', "
            f"got '{receipt['spec_version']}'"
        )
    if receipt["council_id"] != COUNCIL_ID:
        errors.append(
            f"council_id mismatch: expected '{COUNCIL_ID}', "
            f"got '{receipt['council_id']}'"
        )

    seq = receipt.get("ledger_seq")
    if not isinstance(seq, int) or seq < 1:
        errors.append(f"ledger_seq must be positive integer, got {seq!r}")

    seat_id = receipt.get("target_seat_id")
    if not isinstance(seat_id, int) or seat_id not in SEAT_RANGE:
        errors.append(f"target_seat_id must be integer in 1..9, got {seat_id!r}")

    for hash_field in ("entry_sha256", "prev_state_sha256", "next_state_sha256"):
        errors.extend(validate_hash_format(receipt.get(hash_field, ""), hash_field))

    result = receipt.get("result")
    if result not in ("PASS", "FAIL", "ERROR"):
        errors.append(f"result must be 'PASS', 'FAIL', or 'ERROR', got {result!r}")

    verifier = receipt.get("verifier", {})
    if not isinstance(verifier, dict):
        errors.append("verifier must be an object")
    else:
        for vf in ("verifier_id", "public_key"):
            if not verifier.get(vf):
                errors.append(f"verifier.{vf}: missing or empty")

    if errors:
        return "FAIL", "schema_violation", errors

    return "PASS", "receipt_valid", []


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "REPEAT council action/receipt verifier — "
            "deterministic PASS/FAIL/ERROR output."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    action_parser = subparsers.add_parser(
        "verify-action",
        help="Verify a governance action JSON file.",
    )
    action_parser.add_argument(
        "path",
        help="Path to the council action JSON file.",
    )

    receipt_parser = subparsers.add_parser(
        "verify-receipt",
        help="Verify a governance receipt JSON file.",
    )
    receipt_parser.add_argument(
        "path",
        help="Path to the seat_fill receipt JSON file.",
    )

    args = parser.parse_args()

    try:
        data = load_action(args.path)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.command == "verify-action":
        result, reason, errors = verify_action(data)
    else:
        result, reason, errors = verify_receipt(data)

    if result == "PASS":
        print(f"PASS: {reason}")
        return 0

    for err in errors:
        print(f"{result}: {err}", file=sys.stderr)
    print(f"\n{result}: {reason}", file=sys.stderr)
    return 1 if result == "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())
