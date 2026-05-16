"""
hashutil.py — SHA-256 hashing utility for one_string_REPEAT v1.0.
"""
from __future__ import annotations

import hashlib


def sha256_hex(data: bytes) -> str:
    """
    Compute the SHA-256 digest of *data* and return it as a 64-character
    lower-case hex string.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"sha256_hex requires bytes, got {type(data).__name__}")
    return hashlib.sha256(data).hexdigest()
