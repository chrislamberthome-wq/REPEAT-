"""
canonical.py — JCS / RFC 8785 canonicalization for one_string_REPEAT v1.0.

Rules (MUST):
1. Encoding: UTF-8, no BOM.
2. Top-level: must be a JSON object {}.
3. Key order: objects sorted lexicographically by Unicode codepoint (ascending).
4. Whitespace: no insignificant whitespace.
5. Numbers: no NaN, no Infinity.
6. Strings: strict JSON escaping.
7. Arrays: preserve order.
8. Duplicate keys: illegal — raises ValueError.
"""
from __future__ import annotations

import json
from typing import Any


def _detect_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """object_pairs_hook that raises ValueError on duplicate keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate key in JSON object: {key!r}")
        result[key] = value
    return result


def canonicalize(obj: dict[str, Any]) -> bytes:
    """
    Serialize *obj* to canonical UTF-8 JSON bytes (JCS / RFC 8785).

    Raises ValueError if *obj* contains NaN, Infinity, or other non-JSON values.
    """
    if not isinstance(obj, dict):
        raise TypeError(f"canonicalize requires a dict, got {type(obj).__name__}")
    try:
        return json.dumps(
            obj,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Canonicalization failed: {exc}") from exc


def canonicalize_string(s: str) -> bytes:
    """
    Parse a JSON string *s*, check for duplicate keys, then return canonical bytes.

    Raises ValueError on invalid JSON, duplicate keys, or non-JSON number values.
    """
    if not isinstance(s, str):
        raise TypeError(f"canonicalize_string requires str, got {type(s).__name__}")
    try:
        obj = json.loads(s, object_pairs_hook=_detect_duplicates)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError("Payload must be a JSON object ({}), not an array or scalar")
    return canonicalize(obj)
