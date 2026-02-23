"""MRAM receipts verifier.

Checks REPEAT spintronics receipt JSONL files for:
- Required field presence
- sha256: prefix on hash fields
- fail_reason presence when verdict.pass is False
- evidence_hash_sha256 and receipt_hash_sha256 recomputation

Policy: does NOT fail on verdict.pass==false (integrity checks only).
"""
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Optional

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

HASH_FIELDS = ["packet_hash_sha256", "evidence_hash_sha256", "receipt_hash_sha256"]


class VerificationError(Exception):
    """Raised on file access or parse errors (exit code 1)."""


@dataclass
class VerificationResult:
    passed: bool
    count: int
    message: str = field(default="")


def _canonical_json(obj: dict) -> bytes:
    """Canonical JSON per REPEAT C14N v1 (JCS/RFC 8785 compatible)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def _sha256_c14n(obj: dict) -> str:
    """Compute sha256 of canonical JSON, returning 'sha256:<hex>'."""
    digest = hashlib.sha256(_canonical_json(obj)).hexdigest()
    return f"sha256:{digest}"


def _verify_receipt(receipt: dict, line_num: int) -> Optional[str]:
    """Verify a single receipt dict.

    Returns None on success, or an error string describing the first failure.
    """
    # Required fields
    for field_name in REQUIRED_FIELDS:
        if field_name not in receipt:
            return f"line {line_num}: missing required field '{field_name}'"

    # sha256: prefix on hash fields
    for field_name in HASH_FIELDS:
        val = receipt[field_name]
        if not isinstance(val, str) or not val.startswith("sha256:"):
            return (
                f"line {line_num}: field '{field_name}' must have sha256: prefix, "
                f"got: {val!r}"
            )

    # fail_reason required when verdict.pass is False
    verdict = receipt["verdict"]
    if not isinstance(verdict, dict) or "pass" not in verdict:
        return f"line {line_num}: 'verdict' must be an object with 'pass' field"
    if verdict["pass"] is False and "fail_reason" not in verdict:
        return f"line {line_num}: verdict.pass=false but fail_reason is missing"

    # Recompute evidence_hash_sha256:
    # hash is computed over receipt without evidence_hash_sha256 and receipt_hash_sha256
    receipt_without_hashes = {
        k: v for k, v in receipt.items()
        if k not in ("evidence_hash_sha256", "receipt_hash_sha256")
    }
    expected_evidence_hash = _sha256_c14n(receipt_without_hashes)
    if receipt["evidence_hash_sha256"] != expected_evidence_hash:
        return (
            f"line {line_num}: evidence_hash_sha256 mismatch: "
            f"expected {expected_evidence_hash}, "
            f"got {receipt['evidence_hash_sha256']}"
        )

    # Recompute receipt_hash_sha256:
    # hash is computed over receipt with evidence_hash_sha256 but without receipt_hash_sha256
    receipt_without_receipt_hash = {
        k: v for k, v in receipt.items()
        if k != "receipt_hash_sha256"
    }
    expected_receipt_hash = _sha256_c14n(receipt_without_receipt_hash)
    if receipt["receipt_hash_sha256"] != expected_receipt_hash:
        return (
            f"line {line_num}: receipt_hash_sha256 mismatch: "
            f"expected {expected_receipt_hash}, "
            f"got {receipt['receipt_hash_sha256']}"
        )

    return None


def verify_receipts_file(path: str) -> VerificationResult:
    """Verify all receipts in a JSONL file.

    Returns a VerificationResult with passed=True if all receipts pass.
    Raises VerificationError on file access or parse errors (maps to exit code 1).
    Returns VerificationResult(passed=False) on integrity failures (exit code 2).
    """
    if not os.path.exists(path):
        raise VerificationError(f"receipts file not found: {path}")

    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                receipt = json.loads(line)
            except json.JSONDecodeError as e:
                raise VerificationError(f"line {line_num}: JSON parse error: {e}")

            error = _verify_receipt(receipt, line_num)
            if error:
                return VerificationResult(passed=False, count=count, message=error)
            count += 1

    if count == 0:
        return VerificationResult(
            passed=False, count=0, message="no receipts found in file"
        )

    return VerificationResult(passed=True, count=count)
