"""Tests for spintronics canonical module."""

import pytest
from spintronics.canonical import (
    canonicalize_json,
    validate_canonical_form,
    normalize_packet
)


class TestCanonicalizeJson:
    """Tests for canonicalize_json function."""
    
    def test_simple_dict(self):
        """Test canonicalizing a simple dictionary."""
        data = {"b": 2, "a": 1}
        result = canonicalize_json(data)
        assert result == '{"a":1,"b":2}'
    
    def test_nested_dict(self):
        """Test canonicalizing nested dictionaries."""
        data = {"outer": {"b": 2, "a": 1}, "value": 3}
        result = canonicalize_json(data)
        assert result == '{"outer":{"a":1,"b":2},"value":3}'
    
    def test_with_array(self):
        """Test canonicalizing dictionary with arrays."""
        data = {"items": [3, 1, 2], "name": "test"}
        result = canonicalize_json(data)
        assert result == '{"items":[3,1,2],"name":"test"}'
    
    def test_empty_dict(self):
        """Test canonicalizing empty dictionary."""
        result = canonicalize_json({})
        assert result == '{}'


class TestValidateCanonicalForm:
    """Tests for validate_canonical_form function."""
    
    def test_valid_canonical(self):
        """Test validation of canonical JSON."""
        assert validate_canonical_form('{"a":1,"b":2}') is True
    
    def test_invalid_whitespace(self):
        """Test rejection of JSON with whitespace."""
        assert validate_canonical_form('{"a": 1, "b": 2}') is False
    
    def test_invalid_order(self):
        """Test rejection of wrong key order."""
        assert validate_canonical_form('{"b":2,"a":1}') is False
    
    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        assert validate_canonical_form('not json') is False


class TestNormalizePacket:
    """Tests for normalize_packet function."""
    
    def test_normalizes_order(self):
        """Test that keys are sorted after normalization."""
        packet = {"timestamp": "2024-01-01", "id": "abc", "data": "xyz"}
        normalized = normalize_packet(packet)
        keys = list(normalized.keys())
        assert keys == ["data", "id", "timestamp"]
    
    def test_preserves_values(self):
        """Test that values are preserved."""
        packet = {"b": 2, "a": 1}
        normalized = normalize_packet(packet)
        assert normalized["a"] == 1
        assert normalized["b"] == 2
