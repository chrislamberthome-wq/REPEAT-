#!/usr/bin/env python3
"""
python -m verifier

Canonical fail-closed verifier for REPEAT spintronics receipts.

Usage:
    python -m verifier                          # validate mram_receipts.jsonl
    python -m verifier receipts.jsonl           # validate a specific JSONL file
    python -m verifier --help

Exit codes:
    0  All receipts valid (schema + hash checks passed)
    1  One or more receipts failed validation (fail-closed)
"""

import hashlib
import json
import sys
from pathlib import Path

# Path to the receipt schema, relative to repo root
_REPO_ROOT = Path(__file__).parent.parent
_SCHEMA_PATH = _REPO_ROOT / "schemas" / "repeat-spintronics-receipt-v1.schema.json"
_DEFAULT_INPUT = _REPO_ROOT / "mram_receipts.jsonl"

# Required top-level fields in every receipt
_REQUIRED_FIELDS = {
    "schema",
    "packet_hash_sha256",
    "evidence_hash_sha256",
    "receipt_hash_sha256",
    "run_id",
    "measured_resistance_ohms",
    "verdict",
    "metrics",
}


def canonical_json(obj: dict) -> bytes:
    """Canonical JSON bytes per REPEAT C14N v1 (JCS / RFC 8785)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_c14n(obj: dict) -> str:
    """sha256 of canonical JSON bytes, formatted as 'sha256:<hex>'."""
    digest = hashlib.sha256(canonical_json(obj)).hexdigest()
    return f"sha256:{digest}"


def _load_schema(path: Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


def _validate_receipt(receipt: dict, line_num: int) -> list:
    """
    Validate a single receipt dict.  Returns a list of error strings.
    Empty list means the receipt is valid.
    """
    errors = []

    # 1. Required fields
    missing = _REQUIRED_FIELDS - set(receipt.keys())
    if missing:
        errors.append(f"line {line_num}: missing required fields: {sorted(missing)}")
        return errors  # cannot proceed without required fields

    # 2. schema constant
    if receipt.get("schema") != "repeat-spintronics-receipt-v1":
        errors.append(
            f"line {line_num}: schema must be 'repeat-spintronics-receipt-v1', "
            f"got {receipt.get('schema')!r}"
        )

    # 3. Hash format helper
    def _bad_hash(field: str) -> bool:
        v = receipt.get(field, "")
        if not isinstance(v, str):
            return True
        parts = v.split(":", 1)
        return len(parts) != 2 or parts[0] != "sha256" or len(parts[1]) != 64

    for hfield in ("packet_hash_sha256", "evidence_hash_sha256", "receipt_hash_sha256"):
        if _bad_hash(hfield):
            errors.append(
                f"line {line_num}: {hfield} must match 'sha256:<64 hex chars>'"
            )

    if errors:
        return errors

    # 4. Recompute evidence_hash_sha256
    # In simulate_mram_runs.py, evidence_hash is computed BEFORE evidence_hash_sha256
    # and receipt_hash_sha256 are added to the receipt dict, so we exclude both.
    obj_for_evidence = {
        k: v for k, v in receipt.items()
        if k not in ("evidence_hash_sha256", "receipt_hash_sha256")
    }
    expected_evidence = sha256_c14n(obj_for_evidence)
    if receipt["evidence_hash_sha256"] != expected_evidence:
        errors.append(
            f"line {line_num}: evidence_hash_sha256 mismatch — "
            f"stored {receipt['evidence_hash_sha256']!r}, "
            f"recomputed {expected_evidence!r}"
        )

    # 5. Recompute receipt_hash_sha256
    # receipt hash is computed over the receipt including evidence_hash_sha256
    # but NOT including receipt_hash_sha256 itself.
    obj_for_receipt = {k: v for k, v in receipt.items() if k != "receipt_hash_sha256"}
    expected_receipt = sha256_c14n(obj_for_receipt)
    if receipt["receipt_hash_sha256"] != expected_receipt:
        errors.append(
            f"line {line_num}: receipt_hash_sha256 mismatch — "
            f"stored {receipt['receipt_hash_sha256']!r}, "
            f"recomputed {expected_receipt!r}"
        )

    # 6. verdict structure
    verdict = receipt.get("verdict", {})
    if not isinstance(verdict, dict) or "pass" not in verdict:
        errors.append(f"line {line_num}: verdict must be an object with 'pass' field")
    elif not isinstance(verdict["pass"], bool):
        errors.append(f"line {line_num}: verdict.pass must be a boolean")
    elif not verdict["pass"] and "fail_reason" not in verdict:
        errors.append(
            f"line {line_num}: verdict.pass is false but fail_reason is absent"
        )

    # 7. metrics structure
    metrics = receipt.get("metrics", {})
    if not isinstance(metrics, dict):
        errors.append(f"line {line_num}: metrics must be an object")
    else:
        for mfield in ("mean_resistance_ohms", "drift_pct"):
            if mfield not in metrics:
                errors.append(f"line {line_num}: metrics.{mfield} is missing")

    return errors


def verify_file(path: Path) -> int:
    """
    Validate all receipts in a JSONL file.
    Returns 0 if all valid, 1 if any errors found.
    """
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    total = 0
    all_errors = []

    with path.open() as fh:
        for line_num, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                receipt = json.loads(line)
            except json.JSONDecodeError as exc:
                all_errors.append(f"line {line_num}: JSON parse error: {exc}")
                total += 1
                continue

            errors = _validate_receipt(receipt, line_num)
            all_errors.extend(errors)
            total += 1

    if all_errors:
        for err in all_errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(
            f"\nverifier: {len(all_errors)} error(s) in {total} receipt(s) — FAIL",
            file=sys.stderr,
        )
        return 1

    print(f"verifier: {total} receipt(s) validated — PASS")
    return 0


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    input_path = Path(args[0]) if args else _DEFAULT_INPUT
    sys.exit(verify_file(input_path))


if __name__ == "__main__":
    main()
