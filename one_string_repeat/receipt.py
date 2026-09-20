"""
receipt.py — run_receipt generation for one_string_REPEAT v1.0.

Produces a fully populated run_receipt dict from a validated payload dict,
binding the receipt to the canonical payload bytes via SHA-256 and CRC-16.

Fail-closed: any problem during payload validation or execution returns a
receipt with result=ERROR and a non-empty errors list.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .canonical import canonicalize
from .crc16 import crc16_hex
from .engine import execute
from .hashutil import sha256_hex

ENGINE_NAME = "one_string_repeat"
ENGINE_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"

_REQUIRED_PAYLOAD_FIELDS = {
    "schema_version",
    "payload_type",
    "engine_name",
    "engine_version",
    "canonicalization",
    "input_schema",
    "input",
}


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_payload(payload: dict[str, Any]) -> list[str]:
    """Return a list of validation error strings (empty = valid)."""
    errors: list[str] = []
    for field in _REQUIRED_PAYLOAD_FIELDS:
        if field not in payload:
            errors.append(f"missing required payload field: {field!r}")
    if errors:
        return errors
    if payload.get("engine_name") != ENGINE_NAME:
        errors.append(
            f"engine_name mismatch: expected {ENGINE_NAME!r}, "
            f"got {payload['engine_name']!r}"
        )
    if payload.get("engine_version") != ENGINE_VERSION:
        errors.append(
            f"engine_version mismatch: expected {ENGINE_VERSION!r}, "
            f"got {payload['engine_version']!r}"
        )
    if not isinstance(payload.get("input"), dict):
        errors.append("payload 'input' must be a dict")
    return errors


def generate(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a ``run_receipt`` dict from a validated *payload* dict.

    Steps:
    1. Validate payload structure (fail-closed).
    2. Canonicalize payload to bytes.
    3. Compute SHA-256 and CRC-16/CCITT-FALSE from canonical bytes.
    4. Execute the engine.
    5. Compute trace_sha256 from the canonical output bytes.
    6. Return the fully populated run_receipt dict.

    The returned dict always has the run_receipt schema shape.
    ``result`` is "ERROR" and ``errors`` is non-empty if anything fails.
    """
    executed_at = _utc_now_iso()

    def _error_receipt(errs: list[str]) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "receipt_type": "run_receipt",
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "payload_sha256": "",
            "payload_crc16_ccitt_false": "",
            "executed_at": executed_at,
            "result": "ERROR",
            "exit_code": 2,
            "output": {},
            "trace_sha256": "",
            "errors": errs,
        }

    # 1. Structural validation
    if not isinstance(payload, dict):
        return _error_receipt([f"payload must be a dict, got {type(payload).__name__}"])

    validation_errors = _validate_payload(payload)
    if validation_errors:
        return _error_receipt(validation_errors)

    # 2. Canonicalize
    try:
        payload_bytes = canonicalize(payload)
    except (ValueError, TypeError) as exc:
        return _error_receipt([f"canonicalization error: {exc}"])

    # 3. Hash + CRC
    p_sha256 = sha256_hex(payload_bytes)
    p_crc16 = crc16_hex(payload_bytes)

    # 4. Execute
    result, exit_code, output, exec_errors = execute(payload["input"])

    # 5. Trace SHA-256 (canonical serialisation of the output dict)
    try:
        trace_bytes = canonicalize(output) if output else b"{}"
        trace_sha256 = sha256_hex(trace_bytes)
    except (ValueError, TypeError):
        trace_sha256 = ""

    return {
        "schema_version": SCHEMA_VERSION,
        "receipt_type": "run_receipt",
        "engine_name": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "payload_sha256": p_sha256,
        "payload_crc16_ccitt_false": p_crc16,
        "executed_at": executed_at,
        "result": result,
        "exit_code": exit_code,
        "output": output,
        "trace_sha256": trace_sha256,
        "errors": exec_errors,
    }
