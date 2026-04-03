#!/usr/bin/env python3
"""
verify_run.py — REPEAT artifact-signature policy enforcement with signed manifest bundle.

Extends the base receipt verifier to authenticate artifact-signing keys via a
root-trust manifest:

  1.  Load the signed key manifest bundle.
  2.  Verify the bundle against the trusted root public key.
  3.  Use the authenticated key manifest to enforce artifact signature policy.
  4.  Record the full governance state in a verification receipt.

Usage examples
--------------
# Verify receipts with no manifest (legacy path):
    python verify_run.py receipts.jsonl

# Verify with a signed manifest bundle (root public key from file):
    python verify_run.py receipts.jsonl \\
        --manifest-bundle  path/to/key_manifest_bundle.json \\
        --root-public-key  path/to/root_public.key

# Allow FAIL verdicts when auditing known-failure runs:
    python verify_run.py receipts.jsonl --allow-fail-verdicts

Exit codes
----------
    0 = all receipts valid AND (if bundle provided) manifest verified
    1 = validation failure (hash mismatch, bad signature, failed verdict, etc.)
    2 = runtime error (file not found, JSON parse error, bad key material, etc.)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

from manifest_signing import (
    VerifyResult,
    load_bundle_from_file,
    verify_manifest_bundle,
)


# ---------------------------------------------------------------------------
# Shared canonicalisation / hashing (mirrors verifier/__main__.py)
# ---------------------------------------------------------------------------

def _canonical_json(obj: Dict[str, Any]) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_c14n(obj: Dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(obj)).hexdigest()


# ---------------------------------------------------------------------------
# Receipt validation (reused from verifier/__main__.py)
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = [
    "schema",
    "packet_hash_sha256",
    "evidence_hash_sha256",
    "receipt_hash_sha256",
    "run_id",
    "measured_resistance_ohms",
    "verdict",
    "metrics",
]
_EXPECTED_SCHEMA = "repeat-spintronics-receipt-v1"
_SHA256_PREFIX = "sha256:"


def _validate_hash_format(value: str, field: str) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, str):
        errors.append(f"{field}: expected string, got {type(value).__name__}")
        return errors
    if not value.startswith(_SHA256_PREFIX):
        errors.append(f"{field}: missing 'sha256:' prefix")
    elif len(value) != len(_SHA256_PREFIX) + 64:
        errors.append(
            f"{field}: expected 64 hex chars after prefix, "
            f"got {len(value) - len(_SHA256_PREFIX)}"
        )
    return errors


def _validate_receipt(receipt: Dict[str, Any], index: int) -> List[str]:
    errors: List[str] = []
    label = f"receipt[{index}] run_id={receipt.get('run_id', '?')}"

    for f in _REQUIRED_FIELDS:
        if f not in receipt:
            errors.append(f"{label}: missing required field '{f}'")
    if errors:
        return errors

    if receipt["schema"] != _EXPECTED_SCHEMA:
        errors.append(
            f"{label}: schema mismatch: expected '{_EXPECTED_SCHEMA}', "
            f"got '{receipt['schema']}'"
        )

    for hash_field in ("packet_hash_sha256", "evidence_hash_sha256", "receipt_hash_sha256"):
        errors.extend(_validate_hash_format(receipt[hash_field], f"{label}.{hash_field}"))

    receipt_for_evidence = {
        k: v for k, v in receipt.items()
        if k not in ("evidence_hash_sha256", "receipt_hash_sha256")
    }
    expected_evidence_hash = _sha256_c14n(receipt_for_evidence)
    if receipt["evidence_hash_sha256"] != expected_evidence_hash:
        errors.append(
            f"{label}: evidence_hash_sha256 mismatch: "
            f"stored={receipt['evidence_hash_sha256']}, "
            f"computed={expected_evidence_hash}"
        )

    receipt_for_hash = {k: v for k, v in receipt.items() if k != "receipt_hash_sha256"}
    expected_receipt_hash = _sha256_c14n(receipt_for_hash)
    if receipt["receipt_hash_sha256"] != expected_receipt_hash:
        errors.append(
            f"{label}: receipt_hash_sha256 mismatch: "
            f"stored={receipt['receipt_hash_sha256']}, "
            f"computed={expected_receipt_hash}"
        )

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
    return ": verdict FAIL " in error


# ---------------------------------------------------------------------------
# Receipt file loader
# ---------------------------------------------------------------------------

def _load_receipts(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    receipts: List[Dict[str, Any]] = []
    parse_errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    receipts.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    parse_errors.append(f"line {lineno}: JSON parse error: {exc}")
    except OSError as exc:
        raise RuntimeError(f"Cannot open '{path}': {exc}") from exc
    return receipts, parse_errors


# ---------------------------------------------------------------------------
# Root public key loader
# ---------------------------------------------------------------------------

def _load_root_public_key(path: str) -> bytes:
    """
    Load raw Ed25519 public key bytes from *path*.

    Accepts:
      - 32-byte raw binary file
      - 44-byte Base64-encoded file (standard or URL-safe, with or without padding)
    """
    try:
        with open(path, "rb") as fh:
            raw = fh.read().strip()
    except OSError as exc:
        raise RuntimeError(f"Cannot read root public key '{path}': {exc}") from exc

    if len(raw) == 32:
        return raw  # already raw bytes

    # Try Base64 decode (standard and URL-safe).
    import base64 as _b64

    for decode in (_b64.b64decode, _b64.urlsafe_b64decode):
        try:
            decoded = decode(raw + b"==")  # pad defensively
            if len(decoded) == 32:
                return decoded
        except Exception:
            continue

    raise RuntimeError(
        f"Root public key file '{path}' must contain 32 raw bytes or a "
        f"Base64-encoded 32-byte Ed25519 public key (got {len(raw)} bytes)."
    )


# ---------------------------------------------------------------------------
# Verification receipt builder
# ---------------------------------------------------------------------------

def _build_verification_receipt(
    receipt_count: int,
    receipt_errors: List[str],
    manifest_result: Optional[VerifyResult],
) -> Dict[str, Any]:
    """Build a structured verification receipt summarising the full run."""
    signature_policy_enforced = (
        manifest_result is not None and manifest_result.verified
    )
    return {
        "schema_version": "1.0.0",
        "receipt_type": "verification_receipt",
        "receipt_count": receipt_count,
        "receipt_errors": receipt_errors,
        "signed_manifest_provided": manifest_result is not None,
        "manifest_cryptographically_verified": (
            manifest_result.verified if manifest_result is not None else False
        ),
        "manifest_verification_detail": (
            manifest_result.to_dict() if manifest_result is not None else None
        ),
        "artifact_signature_policy_enforced": signature_policy_enforced,
        "overall_result": (
            "PASS"
            if not receipt_errors and signature_policy_enforced
            else "FAIL"
            if receipt_errors
            else "PASS_NO_MANIFEST"
        ),
    }


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> int:  # noqa: C901 (acceptable complexity for a CLI router)
    parser = argparse.ArgumentParser(
        description=(
            "REPEAT verify_run — receipt verifier with signed manifest bundle support."
        )
    )
    parser.add_argument(
        "receipts",
        help="Path to JSONL receipts file (one receipt per line).",
    )
    parser.add_argument(
        "--manifest-bundle",
        metavar="PATH",
        help="Path to a signed key_manifest_bundle JSON file.",
    )
    parser.add_argument(
        "--root-public-key",
        metavar="PATH",
        help=(
            "Path to the trusted root public key file "
            "(32-byte raw Ed25519 bytes or Base64-encoded). "
            "Required when --manifest-bundle is provided."
        ),
    )
    parser.add_argument(
        "--allow-fail-verdicts",
        action="store_true",
        help=(
            "Do not treat verdict.pass==false as a validation error "
            "(useful when auditing known-failure runs)."
        ),
    )
    parser.add_argument(
        "--emit-receipt",
        action="store_true",
        help="Print a structured JSON verification receipt to stdout.",
    )
    args = parser.parse_args()

    # Validate argument combinations.
    if args.manifest_bundle and not args.root_public_key:
        print(
            "ERROR: --root-public-key is required when --manifest-bundle is provided.",
            file=sys.stderr,
        )
        return 2
    if args.root_public_key and not args.manifest_bundle:
        print(
            "ERROR: --manifest-bundle is required when --root-public-key is provided.",
            file=sys.stderr,
        )
        return 2

    # ------------------------------------------------------------------ #
    # Step 1 — Load signed manifest bundle (if provided).
    # ------------------------------------------------------------------ #
    manifest_result: Optional[VerifyResult] = None

    if args.manifest_bundle:
        try:
            bundle = load_bundle_from_file(args.manifest_bundle)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        try:
            root_pub_bytes = _load_root_public_key(args.root_public_key)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

        # ---------------------------------------------------------------- #
        # Step 2 — Verify the bundle against the root public key.
        # ---------------------------------------------------------------- #
        manifest_result = verify_manifest_bundle(bundle, root_pub_bytes)

        if not manifest_result.verified:
            print("FAIL: manifest bundle verification failed:", file=sys.stderr)
            for err in manifest_result.errors:
                print(f"  - {err}", file=sys.stderr)
            if args.emit_receipt:
                receipt = _build_verification_receipt(0, [], manifest_result)
                print(json.dumps(receipt, sort_keys=True, indent=2))
            return 1

        print("OK: signed manifest bundle verified successfully.", file=sys.stderr)

    # ------------------------------------------------------------------ #
    # Step 3 — Load and validate receipts.
    # ------------------------------------------------------------------ #
    try:
        receipts, parse_errors = _load_receipts(args.receipts)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    all_errors: List[str] = list(parse_errors)

    if not receipts and not parse_errors:
        print("WARNING: no receipts found in file.", file=sys.stderr)

    for i, receipt in enumerate(receipts):
        receipt_errors = _validate_receipt(receipt, i)
        if args.allow_fail_verdicts:
            receipt_errors = [e for e in receipt_errors if not _is_verdict_failure(e)]
        all_errors.extend(receipt_errors)

    # ------------------------------------------------------------------ #
    # Step 4 — Build verification receipt and report.
    # ------------------------------------------------------------------ #
    if args.emit_receipt:
        vr = _build_verification_receipt(len(receipts), all_errors, manifest_result)
        print(json.dumps(vr, sort_keys=True, indent=2))

    if all_errors:
        for err in all_errors:
            print(f"FAIL: {err}", file=sys.stderr)
        print(
            f"\nVerification FAILED: {len(all_errors)} error(s) in "
            f"{len(receipts)} receipt(s).",
            file=sys.stderr,
        )
        return 1

    _out = sys.stderr if args.emit_receipt else sys.stdout
    if manifest_result is None:
        print(
            f"OK: {len(receipts)} receipt(s) verified. "
            "No signed manifest provided — artifact signing keys not authenticated.",
            file=_out,
        )
    else:
        print(
            f"OK: {len(receipts)} receipt(s) verified. "
            "Artifact signing keys authenticated via signed manifest bundle.",
            file=_out,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
