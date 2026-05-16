"""
verifier.py — verification_receipt generation for one_string_REPEAT v1.0.

Compares a claimed run_receipt against an independent replay of the same
payload, producing a verification_receipt.

Truth states:
    PASS   — all comparisons match
    FAIL   — replay succeeded but at least one comparison differs
    ERROR  — verification could not be completed

Fail-closed: inability to complete verification is always ERROR, never PASS.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .canonical import canonicalize
from .crc16 import crc16_hex
from .hashutil import sha256_hex
from .replay import replay_from_bytes

VERIFIER_NAME = "one_string_repeat_verifier"
VERIFIER_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

_REQUIRED_RECEIPT_FIELDS = {
    "payload_sha256",
    "payload_crc16_ccitt_false",
    "result",
    "exit_code",
    "output",
}


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify(
    payload: dict[str, Any],
    run_receipt: dict[str, Any],
) -> dict[str, Any]:
    """
    Verify *run_receipt* by replaying *payload* independently.

    Steps:
    1. Canonicalize payload and recompute SHA-256 + CRC-16.
    2. Compare recomputed digests against those claimed in *run_receipt*.
    3. Replay the engine from canonical payload bytes.
    4. Compare replayed result, exit_code, and output against claimed values.
    5. Return a fully populated verification_receipt dict.

    Returns a dict with ``verification_result`` = "ERROR" if the process
    cannot be completed (never silently coerces to PASS).
    """
    verified_at = _utc_now_iso()

    def _error_vr(notes: list[str]) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "receipt_type": "verification_receipt",
            "verifier_name": VERIFIER_NAME,
            "verifier_version": VERIFIER_VERSION,
            "verified_at": verified_at,
            "payload_sha256": "",
            "payload_crc16_ccitt_false": "",
            "claimed_result": run_receipt.get("result", "ERROR") if isinstance(run_receipt, dict) else "ERROR",
            "replayed_result": "ERROR",
            "matched_payload_hash": False,
            "matched_payload_crc16": False,
            "matched_output": False,
            "matched_exit_code": False,
            "verification_result": "ERROR",
            "verification_exit_code": 2,
            "notes": notes,
        }

    # Guard: inputs must be dicts
    if not isinstance(payload, dict):
        return _error_vr([f"payload must be a dict, got {type(payload).__name__}"])
    if not isinstance(run_receipt, dict):
        return _error_vr([f"run_receipt must be a dict, got {type(run_receipt).__name__}"])

    # Check required receipt fields
    missing = _REQUIRED_RECEIPT_FIELDS - run_receipt.keys()
    if missing:
        return _error_vr([f"run_receipt missing required fields: {sorted(missing)}"])

    # 1. Canonicalize payload + recompute digests
    try:
        payload_bytes = canonicalize(payload)
    except (ValueError, TypeError) as exc:
        return _error_vr([f"payload canonicalization error: {exc}"])

    recomputed_sha256 = sha256_hex(payload_bytes)
    recomputed_crc16 = crc16_hex(payload_bytes)

    # 2. Compare digests
    claimed_sha256 = run_receipt.get("payload_sha256", "")
    claimed_crc16 = run_receipt.get("payload_crc16_ccitt_false", "")
    matched_hash = recomputed_sha256 == claimed_sha256
    matched_crc16 = recomputed_crc16 == claimed_crc16

    # 3. Replay
    replayed_result, replayed_exit_code, replayed_output, replay_errors = replay_from_bytes(
        payload_bytes
    )

    # 4. Compare
    claimed_result = run_receipt.get("result", "")
    claimed_exit_code = run_receipt.get("exit_code")
    claimed_output = run_receipt.get("output", {})

    matched_output = replayed_output == claimed_output
    matched_exit_code = replayed_exit_code == claimed_exit_code

    # 5. Determine verification result
    notes: list[str] = []
    if replay_errors:
        notes.extend(f"replay: {e}" for e in replay_errors)

    if not matched_hash:
        notes.append(
            f"SHA-256 mismatch: recomputed={recomputed_sha256!r}, "
            f"claimed={claimed_sha256!r}"
        )
    if not matched_crc16:
        notes.append(
            f"CRC-16 mismatch: recomputed={recomputed_crc16!r}, "
            f"claimed={claimed_crc16!r}"
        )
    if not matched_output:
        notes.append(
            f"output mismatch: replayed={replayed_output!r}, "
            f"claimed={claimed_output!r}"
        )
    if not matched_exit_code:
        notes.append(
            f"exit_code mismatch: replayed={replayed_exit_code!r}, "
            f"claimed={claimed_exit_code!r}"
        )

    if replayed_result == "ERROR":
        verification_result = "ERROR"
        verification_exit_code = 2
    elif matched_hash and matched_crc16 and matched_output and matched_exit_code:
        verification_result = "PASS"
        verification_exit_code = 0
    else:
        verification_result = "FAIL"
        verification_exit_code = 1

    return {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": "verification_receipt",
        "verifier_name": VERIFIER_NAME,
        "verifier_version": VERIFIER_VERSION,
        "verified_at": verified_at,
        "payload_sha256": recomputed_sha256,
        "payload_crc16_ccitt_false": recomputed_crc16,
        "claimed_result": claimed_result,
        "replayed_result": replayed_result,
        "matched_payload_hash": matched_hash,
        "matched_payload_crc16": matched_crc16,
        "matched_output": matched_output,
        "matched_exit_code": matched_exit_code,
        "verification_result": verification_result,
        "verification_exit_code": verification_exit_code,
        "notes": notes,
    }
