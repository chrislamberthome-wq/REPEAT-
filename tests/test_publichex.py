"""Tests for PublicHex v1 verification."""

import pytest
from repeat_hd.cli import (
    encode_data,
    normalize_hex,
    verify_publichex_frame,
    cmd_publichex_verify,
)
import argparse
import json
import sys
from io import StringIO


class TestNormalizeHex:
    """Tests for normalize_hex function."""
    
    def test_normalize_removes_whitespace(self):
        """Test that whitespace is removed during normalization."""
        hex_input = "82 89 d1 f7 05 00 00 00 48 65 6c 6c 6f"
        normalized, errors = normalize_hex(hex_input)
        
        assert errors == []
        assert " " not in normalized
        assert normalized == "8289d1f70500000048656c6c6f"
    
    def test_normalize_converts_to_lowercase(self):
        """Test that uppercase is converted to lowercase."""
        hex_input = "8289D1F70500000048656C6C6F"
        normalized, errors = normalize_hex(hex_input)
        
        assert errors == []
        assert normalized == "8289d1f70500000048656c6c6f"
    
    def test_normalize_handles_newlines_and_tabs(self):
        """Test that various whitespace types are handled."""
        hex_input = "8289\nd1f7\t0500\r\n000048656c6c6f"
        normalized, errors = normalize_hex(hex_input)
        
        assert errors == []
        assert normalized == "8289d1f70500000048656c6c6f"
    
    def test_normalize_detects_invalid_characters(self):
        """Test that invalid hex characters are detected."""
        hex_input = "G1H2I3J4"
        normalized, errors = normalize_hex(hex_input)
        
        assert len(errors) > 0
        assert normalized == ""
        assert "invalid" in errors[0].lower()
    
    def test_normalize_empty_string(self):
        """Test normalization of empty string."""
        hex_input = ""
        normalized, errors = normalize_hex(hex_input)
        
        assert errors == []
        assert normalized == ""
    
    def test_normalize_only_whitespace(self):
        """Test normalization of only whitespace."""
        hex_input = "   \n\t\r\n  "
        normalized, errors = normalize_hex(hex_input)
        
        assert errors == []
        assert normalized == ""


class TestVerifyPublicHexFrame:
    """Tests for verify_publichex_frame function."""
    
    def test_verify_valid_frame(self):
        """Test verification of a valid frame."""
        # Create a valid frame
        original = "Hello"
        encoded = encode_data(original)
        hex_string = encoded.hex()
        
        is_valid, errors = verify_publichex_frame(hex_string)
        
        assert is_valid
        assert errors == []
    
    def test_verify_frame_too_short(self):
        """Test that too-short frames are rejected."""
        hex_string = "123456"  # Only 3 bytes, need at least 8
        
        is_valid, errors = verify_publichex_frame(hex_string)
        
        assert not is_valid
        assert len(errors) > 0
        assert "too short" in errors[0].lower()
    
    def test_verify_frame_odd_length(self):
        """Test that odd-length hex strings are rejected."""
        hex_string = "123"  # Odd number of characters
        
        is_valid, errors = verify_publichex_frame(hex_string)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_verify_frame_invalid_crc(self):
        """Test that frames with invalid CRC are rejected."""
        # Create a valid frame then corrupt the CRC
        original = "test"
        encoded = encode_data(original)
        hex_string = "ffffffff" + encoded.hex()[8:]
        
        is_valid, errors = verify_publichex_frame(hex_string)
        
        assert not is_valid
        assert len(errors) > 0
        assert "crc" in errors[0].lower()
    
    def test_verify_frame_invalid_length(self):
        """Test that frames with invalid length field are rejected."""
        # Create a frame with wrong length field
        hex_string = "8289d1f7ff00000048656c6c6f"  # Length field says 255 bytes
        
        is_valid, errors = verify_publichex_frame(hex_string)
        
        assert not is_valid
        assert len(errors) > 0


class TestPublicHexVerifyCommand:
    """Tests for cmd_publichex_verify function."""
    
    def test_verify_pass_with_valid_hex(self, capsys):
        """Test PASS case with valid hex."""
        # Create valid hex
        original = "test data"
        encoded = encode_data(original)
        hex_string = encoded.hex()
        
        args = argparse.Namespace(hex=hex_string)
        result = cmd_publichex_verify(args)
        
        assert result == 0  # PASS
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_verify_pass_with_whitespace(self, capsys):
        """Test PASS case with whitespace in hex."""
        # Create valid hex with whitespace
        original = "test"
        encoded = encode_data(original)
        hex_string = encoded.hex()
        hex_with_whitespace = " ".join([hex_string[i:i + 2] for i in range(0, len(hex_string), 2)])
        
        args = argparse.Namespace(hex=hex_with_whitespace)
        result = cmd_publichex_verify(args)
        
        assert result == 0  # PASS
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["encoding"] == "publichex-v1"
        assert " " not in output["normalized_frame_hex"]
        assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_verify_pass_with_uppercase(self, capsys):
        """Test PASS case with uppercase hex."""
        # Create valid hex in uppercase
        original = "TEST"
        encoded = encode_data(original)
        hex_string = encoded.hex().upper()
        
        args = argparse.Namespace(hex=hex_string)
        result = cmd_publichex_verify(args)
        
        assert result == 0  # PASS
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_verify_fail_with_invalid_crc(self, capsys):
        """Test FAIL case with invalid CRC."""
        # Create hex with invalid CRC
        original = "test"
        encoded = encode_data(original)
        hex_string = "ffffffff" + encoded.hex()[8:]
        
        args = argparse.Namespace(hex=hex_string)
        result = cmd_publichex_verify(args)
        
        assert result == 2  # FAIL
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_verify_error_with_invalid_chars(self, capsys):
        """Test ERROR case with invalid characters."""
        args = argparse.Namespace(hex="GHIJKLMN")
        result = cmd_publichex_verify(args)
        
        assert result == 1  # ERROR
    
    def test_verify_stdin_input(self, monkeypatch, capsys):
        """Test reading from stdin."""
        # Create valid hex
        original = "stdin test"
        encoded = encode_data(original)
        hex_string = encoded.hex()
        
        # Mock stdin
        monkeypatch.setattr('sys.stdin', StringIO(hex_string))
        
        args = argparse.Namespace(hex=None)
        result = cmd_publichex_verify(args)
        
        assert result == 0  # PASS
        
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["normalized_frame_hex"] == hex_string.lower()


class TestPublicHexIntegration:
    """Integration tests for PublicHex verification."""
    
    def test_roundtrip_encode_to_publichex_verify(self, capsys):
        """Test encoding data and verifying it with publichex-verify."""
        test_cases = [
            "Hello, World!",
            "Short",
            "",
            "Unicode: 世界 🌍",
            "Numbers: 1234567890",
        ]
        
        for original in test_cases:
            encoded = encode_data(original)
            hex_string = encoded.hex()
            
            args = argparse.Namespace(hex=hex_string)
            result = cmd_publichex_verify(args)
            
            assert result == 0, f"Failed for: {original}"
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["encoding"] == "publichex-v1"
            assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_whitespace_injection_preserves_validity(self, capsys):
        """Test that injecting whitespace into valid hex preserves PASS result."""
        original = "whitespace test"
        encoded = encode_data(original)
        hex_string = encoded.hex()
        
        # Test various whitespace patterns
        whitespace_variants = [
            hex_string,  # No whitespace
            " ".join([hex_string[i:i + 2] for i in range(0, len(hex_string), 2)]),  # Space every 2 chars
            " ".join([hex_string[i:i + 4] for i in range(0, len(hex_string), 4)]),  # Space every 4 chars
            hex_string[:8] + "\n" + hex_string[8:16] + "\t" + hex_string[16:],  # Mixed whitespace
        ]
        
        for variant in whitespace_variants:
            args = argparse.Namespace(hex=variant)
            result = cmd_publichex_verify(args)
            
            assert result == 0, f"Failed for variant: {repr(variant)}"
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["normalized_frame_hex"] == hex_string.lower()
    
    def test_case_insensitive_normalization(self, capsys):
        """Test that case variations normalize to canonical lowercase."""
        original = "Case Test"
        encoded = encode_data(original)
        hex_lower = encoded.hex().lower()
        hex_upper = encoded.hex().upper()
        hex_mixed = "".join([c.upper() if i % 2 == 0 else c.lower()
                            for i, c in enumerate(encoded.hex())])
        
        for variant in [hex_lower, hex_upper, hex_mixed]:
            args = argparse.Namespace(hex=variant)
            result = cmd_publichex_verify(args)
            
            assert result == 0
            
            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["normalized_frame_hex"] == hex_lower
    
    def test_fail_vectors(self, capsys):
        """Test that FAIL vectors correctly yield FAIL result."""
        # Create various failure cases
        valid_encoded = encode_data("test")
        valid_hex = valid_encoded.hex()
        
        fail_cases = [
            # Corrupted CRC
            "ffffffff" + valid_hex[8:],
            # Wrong length field
            "8289d1f7ff00000048656c6c6f",
            # Length mismatch (header says 10 bytes but only 5 bytes provided)
            valid_hex[:8] + "0a000000" + valid_hex[16:16 + 10],
        ]
        
        for fail_hex in fail_cases:
            args = argparse.Namespace(hex=fail_hex)
            result = cmd_publichex_verify(args)
            
            # Should be FAIL (exit code 2), not ERROR (exit code 1)
            assert result == 2, f"Expected FAIL for: {fail_hex}"
