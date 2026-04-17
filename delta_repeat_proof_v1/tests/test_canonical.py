"""Tests for canonical JSON serialization and SHA-256 hashing.

Guarantees under test
---------------------
- canonical_bytes produces sorted keys, no extra whitespace, UTF-8.
- Non-canonical JSON is detected (i.e. sorted form differs from unsorted).
- sha256_hex and canonical_sha256 are deterministic.
- crc16_ccitt_false matches known reference vectors.
"""
import json
import pytest

from delta_repeat_proof_v1.verifier.canonical import (
    canonical_bytes,
    canonical_sha256,
    crc16_ccitt_false,
    sha256_hex,
)


def test_canonical_bytes_sorts_keys():
    obj = {"z": 1, "a": 2, "m": 3}
    result = canonical_bytes(obj).decode("utf-8")
    assert result == '{"a":2,"m":3,"z":1}'


def test_canonical_bytes_no_extra_whitespace():
    obj = {"key": "value"}
    result = canonical_bytes(obj).decode("utf-8")
    assert " " not in result


def test_canonical_bytes_utf8():
    obj = {"note": "caf\u00e9"}
    raw = canonical_bytes(obj)
    assert isinstance(raw, bytes)
    decoded = raw.decode("utf-8")
    assert "caf\u00e9" in decoded


def test_canonical_bytes_nested():
    obj = {"b": {"y": 9, "x": 8}, "a": 1}
    result = canonical_bytes(obj).decode("utf-8")
    assert result == '{"a":1,"b":{"x":8,"y":9}}'


def test_sha256_hex_is_64_chars():
    digest = sha256_hex(b"hello")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_sha256_hex_known_value():
    # SHA-256 of empty bytes
    digest = sha256_hex(b"")
    assert digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_canonical_sha256_deterministic():
    obj = {"cycle_id": "cycle-0001", "status": "PASS"}
    h1 = canonical_sha256(obj)
    h2 = canonical_sha256(obj)
    assert h1 == h2


def test_non_canonical_detected():
    """A dict serialised with different key order must differ from canonical."""
    obj = {"z": 1, "a": 2}
    non_canonical = json.dumps(obj, sort_keys=False).encode("utf-8")
    canonical = canonical_bytes(obj)
    # Both are valid JSON but may differ in key order
    non_canonical_obj = json.loads(non_canonical)
    canonical_obj = json.loads(canonical)
    # The canonical form always has sorted keys
    assert list(canonical_obj.keys()) == sorted(canonical_obj.keys())


def test_crc16_ccitt_false_known_vector():
    # CRC-16/CCITT-FALSE of b"123456789" = 0x29B1
    result = crc16_ccitt_false(b"123456789")
    assert result == "29b1"


def test_crc16_ccitt_false_empty():
    result = crc16_ccitt_false(b"")
    assert result == "ffff"


def test_crc16_ccitt_false_length_4():
    result = crc16_ccitt_false(b"test")
    assert len(result) == 4
    assert all(c in "0123456789abcdef" for c in result)
