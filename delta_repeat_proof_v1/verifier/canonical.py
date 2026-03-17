"""Canonical JSON serialization and SHA-256 / CRC-16 hashing.

All serialization follows JCS (RFC 8785): keys sorted lexicographically,
no insignificant whitespace, UTF-8 encoding.  Non-canonical input is
rejected — there is no best-effort fallback.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """Return the canonical UTF-8 JSON encoding of *obj*.

    Keys are sorted; no extra whitespace; ASCII escaping disabled so
    Unicode characters are preserved verbatim.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def canonical_sha256(obj: Any) -> str:
    """Return the SHA-256 hex digest of the canonical JSON of *obj*."""
    return sha256_hex(canonical_bytes(obj))


def crc16_ccitt_false(data: bytes) -> str:
    """Return the 4-hex-char CRC-16/CCITT-FALSE checksum of *data*.

    Parameters: poly=0x1021, init=0xFFFF, refin=False, refout=False,
    xorout=0x0000.
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, "04x")
