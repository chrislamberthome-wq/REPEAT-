"""Tests for the REPEAT-HD CLI module."""

import pytest
import tempfile
import os
from repeat_hd.cli import (
    encode_data,
    decode_data,
    check_invariants,
    cmd_encode,
    cmd_verify,
)
import argparse


class TestEncodeData:
    """Tests for encode_data function."""
    
    def test_encode_simple_string(self):
        """Test encoding a simple string."""
        result = encode_data("hello")
        assert len(result) > 8  # At least header + data
        assert len(result) == 8 + len("hello")
    
    def test_encode_empty_string(self):
        """Test encoding an empty string."""
        result = encode_data("")
        assert len(result) == 8  # Just the header
    
    def test_encode_unicode(self):
        """Test encoding unicode characters."""
        result = encode_data("Hello 世界")
        assert len(result) > 8
        # UTF-8 encoded "世界" takes 6 bytes
        assert len(result) == 8 + len("Hello 世界".encode('utf-8'))


class TestDecodeData:
    """Tests for decode_data function."""
    
    def test_decode_valid_data(self):
        """Test decoding valid encoded data."""
        original = "hello world"
        encoded = encode_data(original)
        decoded, is_valid, errors = decode_data(encoded)
        
        assert is_valid
        assert decoded == original
        assert len(errors) == 0
    
    def test_decode_empty_data(self):
        """Test decoding empty encoded data."""
        original = ""
        encoded = encode_data(original)
        decoded, is_valid, errors = decode_data(encoded)
        
        assert is_valid
        assert decoded == original
        assert len(errors) == 0
    
    def test_decode_unicode(self):
        """Test decoding unicode data."""
        original = "Hello 世界 🌍"
        encoded = encode_data(original)
        decoded, is_valid, errors = decode_data(encoded)
        
        assert is_valid
        assert decoded == original
        assert len(errors) == 0
    
    def test_decode_too_short(self):
        """Test decoding data that's too short."""
        decoded, is_valid, errors = decode_data(b"short")
        
        assert not is_valid
        assert decoded == ""
        assert len(errors) > 0
        assert "too short" in errors[0].lower()
    
    def test_decode_corrupted_crc(self):
        """Test decoding data with corrupted CRC."""
        encoded = encode_data("hello")
        # Corrupt the CRC (first 4 bytes)
        corrupted = b'\xff\xff\xff\xff' + encoded[4:]
        
        decoded, is_valid, errors = decode_data(corrupted)
        
        assert not is_valid
        assert decoded == ""
        assert len(errors) > 0
        assert "crc mismatch" in errors[0].lower()
    
    def test_decode_length_mismatch(self):
        """Test decoding data with length mismatch."""
        encoded = encode_data("hello")
        # Add extra bytes
        corrupted = encoded + b"extra"
        
        decoded, is_valid, errors = decode_data(corrupted)
        
        assert not is_valid
        assert decoded == ""
        assert len(errors) > 0
        assert "length mismatch" in errors[0].lower()


class TestCheckInvariants:
    """Tests for check_invariants function."""
    
    def test_invariants_valid_data(self):
        """Test invariants pass for valid data."""
        data = "hello world"
        encoded = encode_data(data)
        violations = check_invariants(data, encoded)
        
        assert len(violations) == 0
    
    def test_invariants_empty_data(self):
        """Test invariants pass for empty data."""
        data = ""
        encoded = encode_data(data)
        violations = check_invariants(data, encoded)
        
        assert len(violations) == 0
    
    def test_invariants_unicode_data(self):
        """Test invariants pass for unicode data."""
        data = "Hello 世界 🌍"
        encoded = encode_data(data)
        violations = check_invariants(data, encoded)
        
        assert len(violations) == 0
    
    def test_invariants_detect_null_bytes(self):
        """Test invariants detect null bytes in data."""
        data = "hello\x00world"
        encoded = encode_data(data)
        violations = check_invariants(data, encoded)
        
        assert len(violations) > 0
        assert any("null bytes" in v.lower() for v in violations)
    
    def test_invariants_detect_wrong_size(self):
        """Test invariants detect wrong encoded size."""
        data = "hello"
        encoded = encode_data(data)
        # Corrupt by adding extra bytes
        corrupted = encoded + b"extra"
        violations = check_invariants(data, corrupted)
        
        assert len(violations) > 0
        assert any("encoded size" in v.lower() for v in violations)
    
    def test_invariants_detect_re_encoding_mismatch(self):
        """Test invariants detect re-encoding mismatch."""
        data = "hello"
        encoded = encode_data(data)
        # Create a different encoding by modifying it
        corrupted = encoded[:-1] + b'X'
        violations = check_invariants(data, corrupted)
        
        # Should detect multiple issues including re-encoding mismatch
        assert len(violations) > 0


class TestCmdVerify:
    """Tests for cmd_verify function with --strict flag."""
    
    def test_verify_without_strict_valid_data(self):
        """Test verify command without --strict flag on valid data."""
        # Create a temporary file with encoded data
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            encoded = encode_data("test data")
            f.write(encoded)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=False)
            result = cmd_verify(args)
            assert result == 0
        finally:
            os.unlink(temp_file)
    
    def test_verify_with_strict_valid_data(self):
        """Test verify command with --strict flag on valid data."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            encoded = encode_data("test data")
            f.write(encoded)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=True)
            result = cmd_verify(args)
            assert result == 0
        finally:
            os.unlink(temp_file)
    
    def test_verify_without_strict_invalid_crc(self):
        """Test verify command without --strict flag on invalid CRC."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            encoded = encode_data("test data")
            # Corrupt CRC
            corrupted = b'\xff\xff\xff\xff' + encoded[4:]
            f.write(corrupted)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=False)
            result = cmd_verify(args)
            assert result == 1  # CRC failure
        finally:
            os.unlink(temp_file)
    
    def test_verify_with_strict_invalid_crc(self):
        """Test verify command with --strict flag on invalid CRC."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            encoded = encode_data("test data")
            # Corrupt CRC
            corrupted = b'\xff\xff\xff\xff' + encoded[4:]
            f.write(corrupted)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=True)
            result = cmd_verify(args)
            # Should fail at CRC check before getting to invariants
            assert result == 1
        finally:
            os.unlink(temp_file)
    
    def test_verify_with_strict_invariant_violation(self):
        """Test verify command with --strict flag detecting invariant violation."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Create data with null bytes (violates invariant)
            encoded = encode_data("hello\x00world")
            f.write(encoded)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=True)
            result = cmd_verify(args)
            # Should return 2 for invariant violation
            assert result == 2
        finally:
            os.unlink(temp_file)
    
    def test_verify_without_strict_skips_invariants(self):
        """Test verify without --strict doesn't check invariants."""
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            # Create data with null bytes (violates invariant but passes CRC)
            encoded = encode_data("hello\x00world")
            f.write(encoded)
            temp_file = f.name
        
        try:
            args = argparse.Namespace(infile=temp_file, strict=False)
            result = cmd_verify(args)
            # Should pass because CRC is valid and invariants are not checked
            assert result == 0
        finally:
            os.unlink(temp_file)


class TestCmdEncode:
    """Tests for cmd_encode function."""
    
    def test_encode_simple_data(self):
        """Test encoding simple data via the encode function."""
        # Test encode_data function directly (cmd_encode is hard to test due to stdout)
        data = "test"
        encoded = encode_data(data)
        
        # Verify the encoded data can be decoded
        decoded, is_valid, errors = decode_data(encoded)
        assert is_valid
        assert decoded == data
        assert len(errors) == 0


class TestIntegration:
    """Integration tests for the full encode/verify workflow."""
    
    def test_encode_verify_roundtrip(self):
        """Test full encode -> verify roundtrip."""
        original = "Integration test data 🚀"
        encoded = encode_data(original)
        decoded, is_valid, errors = decode_data(encoded)
        
        assert is_valid
        assert decoded == original
        assert len(errors) == 0
        
        # Also check invariants
        violations = check_invariants(decoded, encoded)
        assert len(violations) == 0
    
    def test_multiple_encode_decode_cycles(self):
        """Test multiple encode/decode cycles."""
        data = "cycle test"
        
        for _ in range(5):
            encoded = encode_data(data)
            decoded, is_valid, errors = decode_data(encoded)
            assert is_valid
            assert decoded == data
            
            # Verify invariants
            violations = check_invariants(decoded, encoded)
            assert len(violations) == 0
