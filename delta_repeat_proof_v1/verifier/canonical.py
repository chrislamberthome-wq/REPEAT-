"""Canonical JSON serialisation (RFC 8785 subset) and SHA-256 hashing."""
import hashlib
import json
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """Return deterministic UTF-8 bytes for *obj* using RFC 8785 rules.

    Keys are lexicographically sorted; no insignificant whitespace; no BOM.
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    """Return ``sha256:<hex>`` for *data*."""
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical_hash(obj: Any) -> str:
    """Return ``sha256:<hex>`` of the canonical JSON of *obj*."""
    return sha256_hex(canonical_bytes(obj))
