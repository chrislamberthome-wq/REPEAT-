"""Tests for REPEAT-HD CLI."""

import pytest
from repeat_hd.cli import encode, verify


def test_encode():
    """Test encoding functionality."""
    result = encode("hello")
    assert "hello:" in result
    assert len(result) > len("hello")


def test_verify_valid():
    """Test verification of valid encoded text."""
    encoded = encode("hello")
    assert verify(encoded) is True


def test_verify_invalid():
    """Test verification of invalid encoded text."""
    assert verify("hello:wrongchecksum") is False


def test_verify_no_checksum():
    """Test verification of text without checksum."""
    assert verify("hello") is False


def test_encode_decode_roundtrip():
    """Test that encode and verify work together."""
    text = "test message"
    encoded = encode(text)
    assert verify(encoded) is True
