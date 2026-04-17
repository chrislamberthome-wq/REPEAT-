"""Receipt construction and verification.

A receipt is a compact, tamper-evident summary of one completed cycle.
It captures: the trace hash, event count, governance verdict, replay
outcome, overall status, and a CRC-16 checksum of the core fields.

Construction
------------
``build_receipt`` computes all derived fields from scratch; callers
supply the raw inputs.

Verification
------------
``verify_receipt`` re-derives every computed field and compares it to
the stored receipt; any discrepancy is a hard failure.
"""
from __future__ import annotations

import json
from typing import Any, Dict

from .canonical import canonical_bytes, crc16_ccitt_false, sha256_hex


def build_receipt(
    *,
    cycle_id: str,
    trace_bytes: bytes,
    event_count: int,
    governance_verdict: str,
    replay_match: bool,
    status: str,
) -> Dict[str, Any]:
    """Build a receipt dict with all derived fields computed."""
    trace_sha256 = sha256_hex(trace_bytes)
    core = {
        "cycle_id": cycle_id,
        "event_count": event_count,
        "governance_verdict": governance_verdict,
        "replay_match": replay_match,
        "status": status,
        "trace_sha256": trace_sha256,
    }
    crc = crc16_ccitt_false(canonical_bytes(core))
    receipt = dict(core)
    receipt["crc16_ccitt_false"] = crc
    return receipt


class ReceiptVerificationError(Exception):
    """Raised when a stored receipt fails re-derivation."""


def verify_receipt(stored: Dict[str, Any], trace_bytes: bytes) -> None:
    """Re-derive all computed receipt fields and compare to *stored*.

    Raises
    ------
    ReceiptVerificationError
        If any field does not match the re-derived value.
    """
    errors = []

    expected_trace_sha256 = sha256_hex(trace_bytes)
    if stored.get("trace_sha256") != expected_trace_sha256:
        errors.append(
            f"trace_sha256 mismatch: stored={stored.get('trace_sha256')!r}, "
            f"expected={expected_trace_sha256!r}"
        )

    core = {
        "cycle_id": stored["cycle_id"],
        "event_count": stored["event_count"],
        "governance_verdict": stored["governance_verdict"],
        "replay_match": stored["replay_match"],
        "status": stored["status"],
        "trace_sha256": stored["trace_sha256"],
    }
    expected_crc = crc16_ccitt_false(canonical_bytes(core))
    if stored.get("crc16_ccitt_false") != expected_crc:
        errors.append(
            f"crc16_ccitt_false mismatch: stored={stored.get('crc16_ccitt_false')!r}, "
            f"expected={expected_crc!r}"
        )

    if errors:
        raise ReceiptVerificationError("; ".join(errors))
