"""
replay.py — deterministic replay for one_string_REPEAT v1.0.

Replays a run from its canonical payload bytes, producing an independent
(result, exit_code, output, errors) tuple that the verifier uses to
compare against a claimed run_receipt.

Fail-closed: any problem returns ("ERROR", 2, {}, [error_message]).
"""
from __future__ import annotations

import json
from typing import Any

from .canonical import canonicalize, _detect_duplicates
from .engine import execute

_RESULT_ERROR = "ERROR"
_EXIT_ERROR = 2


def replay_from_bytes(payload_bytes: bytes) -> tuple[str, int, dict[str, Any], list[str]]:
    """
    Re-execute the engine from raw canonical *payload_bytes*.

    Returns ``(result, exit_code, output, errors)``.
    """
    if not isinstance(payload_bytes, (bytes, bytearray)):
        return _RESULT_ERROR, _EXIT_ERROR, {}, [
            f"replay_from_bytes requires bytes, got {type(payload_bytes).__name__}"
        ]

    # Parse the canonical bytes back to a dict, detecting duplicate keys
    try:
        payload_str = payload_bytes.decode("utf-8")
        payload = json.loads(payload_str, object_pairs_hook=_detect_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return _RESULT_ERROR, _EXIT_ERROR, {}, [f"payload parse error during replay: {exc}"]

    if not isinstance(payload, dict):
        return _RESULT_ERROR, _EXIT_ERROR, {}, [
            "payload must be a JSON object for replay"
        ]

    # Re-canonicalize and compare to confirm bytes are stable
    try:
        recanon = canonicalize(payload)
    except (ValueError, TypeError) as exc:
        return _RESULT_ERROR, _EXIT_ERROR, {}, [f"re-canonicalization error: {exc}"]

    if recanon != payload_bytes:
        return _RESULT_ERROR, _EXIT_ERROR, {}, [
            "canonical bytes are not stable (re-canonicalization mismatch)"
        ]

    input_obj = payload.get("input")
    if not isinstance(input_obj, dict):
        return _RESULT_ERROR, _EXIT_ERROR, {}, ["missing or invalid 'input' in payload"]

    return execute(input_obj)


def replay_from_payload(payload: dict[str, Any]) -> tuple[str, int, dict[str, Any], list[str]]:
    """
    Re-execute the engine from a payload dict.

    Canonicalizes *payload* first, then calls :func:`replay_from_bytes`.
    """
    try:
        payload_bytes = canonicalize(payload)
    except (ValueError, TypeError) as exc:
        return _RESULT_ERROR, _EXIT_ERROR, {}, [f"canonicalization error: {exc}"]
    return replay_from_bytes(payload_bytes)
