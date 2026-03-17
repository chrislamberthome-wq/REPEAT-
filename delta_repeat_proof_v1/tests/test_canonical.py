"""Tests for verifier.canonical (RFC 8785 subset)."""
import pytest

from verifier.canonical import canonical_bytes, canonical_hash, sha256_hex


def test_canonical_sorts_keys():
    assert canonical_bytes({"z": 1, "a": 2}) == b'{"a":2,"z":1}'


def test_canonical_no_whitespace():
    result = canonical_bytes({"a": 1, "b": [2, 3]})
    assert b" " not in result


def test_canonical_nested_sorts_keys():
    obj = {"outer": {"z": 9, "a": 1}}
    assert canonical_bytes(obj) == b'{"outer":{"a":1,"z":9}}'


def test_canonical_array_order_preserved():
    obj = {"items": [3, 1, 2]}
    assert canonical_bytes(obj) == b'{"items":[3,1,2]}'


def test_canonical_bool_lowercase():
    assert canonical_bytes({"flag": True}) == b'{"flag":true}'
    assert canonical_bytes({"flag": False}) == b'{"flag":false}'


def test_canonical_null():
    assert canonical_bytes({"x": None}) == b'{"x":null}'


def test_canonical_hash_format():
    h = canonical_hash({"test": "value"})
    assert h.startswith("sha256:")
    assert len(h) == 71  # "sha256:" (7) + 64 hex chars


def test_canonical_hash_deterministic():
    obj1 = {"b": 2, "a": 1}
    obj2 = {"a": 1, "b": 2}
    assert canonical_hash(obj1) == canonical_hash(obj2)


def test_sha256_hex_format():
    h = sha256_hex(b"hello")
    assert h.startswith("sha256:")
    assert len(h) == 71


def test_canonical_nan_rejected():
    import math

    with pytest.raises((ValueError, OverflowError)):
        canonical_bytes({"x": math.nan})
