"""Tests for PublicHex v1 functionality."""

import pytest
import json
import subprocess
import sys


class TestNormalizeHex:
    """Tests for the normalize_hex function."""
    
    def test_normalize_uppercase_to_lowercase(self):
        """Test that uppercase hex is normalized to lowercase."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DEADBEEF")
        assert is_valid
        assert normalized == "deadbeef"
        assert error == ""
    
    def test_normalize_with_spaces(self):
        """Test that spaces are removed during normalization."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DE AD BE EF")
        assert is_valid
        assert normalized == "deadbeef"
        assert error == ""
    
    def test_normalize_with_tabs_and_newlines(self):
        """Test that tabs and newlines are removed."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DE\tAD\nBE\rEF")
        assert is_valid
        assert normalized == "deadbeef"
        assert error == ""
    
    def test_normalize_mixed_case(self):
        """Test normalization with mixed case."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DeAdBeEf")
        assert is_valid
        assert normalized == "deadbeef"
        assert error == ""
    
    def test_fail_odd_length(self):
        """Test that odd length hex string fails."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DEADBEE")
        assert not is_valid
        assert normalized == ""
        assert "odd number" in error.lower()
    
    def test_fail_invalid_character(self):
        """Test that invalid hex characters fail."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("DEADBEEG")
        assert not is_valid
        assert normalized == ""
        assert "non-hexadecimal" in error.lower()
    
    def test_fail_empty_string(self):
        """Test that empty string fails."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("")
        assert not is_valid
        assert normalized == ""
        assert "empty" in error.lower()
    
    def test_fail_whitespace_only(self):
        """Test that whitespace-only input fails."""
        from repeat_hd.cli import normalize_hex
        
        normalized, is_valid, error = normalize_hex("   \t\n  ")
        assert not is_valid
        assert normalized == ""
        assert "empty" in error.lower()


class TestPublicHexVerifyCLI:
    """Tests for the publichex-verify CLI command."""
    
    def run_publichex_verify(self, hex_input=None, use_stdin=False):
        """Helper to run publichex-verify command."""
        cmd = [sys.executable, "-m", "repeat_hd.cli", "publichex-verify"]
        
        if hex_input and not use_stdin:
            cmd.extend(["--hex", hex_input])
            result = subprocess.run(cmd, capture_output=True, text=True)
        elif hex_input and use_stdin:
            result = subprocess.run(cmd, input=hex_input, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        return result.returncode, result.stdout, result.stderr
    
    def test_pass_simple_hex(self):
        """Test PASS with simple hexadecimal."""
        exit_code, stdout, stderr = self.run_publichex_verify("DEADBEEF")
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "deadbeef"
    
    def test_pass_with_whitespace(self):
        """Test PASS with whitespace that should be removed."""
        exit_code, stdout, stderr = self.run_publichex_verify("DE AD BE EF")
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "deadbeef"
    
    def test_pass_with_various_whitespace(self):
        """Test PASS with tabs, newlines, and spaces."""
        exit_code, stdout, stderr = self.run_publichex_verify("48\t65\n6C\r6C\n6F")
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "48656c6c6f"
    
    def test_pass_lowercase_hex(self):
        """Test PASS with already lowercase hex."""
        exit_code, stdout, stderr = self.run_publichex_verify("deadbeef")
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "deadbeef"
    
    def test_pass_via_stdin(self):
        """Test PASS using stdin input."""
        exit_code, stdout, stderr = self.run_publichex_verify("48656C6C6F", use_stdin=True)
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "48656c6c6f"
    
    def test_pass_stdin_with_whitespace(self):
        """Test PASS via stdin with whitespace injection."""
        exit_code, stdout, stderr = self.run_publichex_verify("48 65 6C 6C 6F", use_stdin=True)
        
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["encoding"] == "publichex-v1"
        assert output["normalized_frame_hex"] == "48656c6c6f"
    
    def test_fail_odd_length(self):
        """Test FAIL with odd number of characters."""
        exit_code, stdout, stderr = self.run_publichex_verify("DEADBEE")
        
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
        assert "odd number" in output["error"].lower()
    
    def test_fail_invalid_character(self):
        """Test FAIL with invalid hex character."""
        exit_code, stdout, stderr = self.run_publichex_verify("DEADBEEG")
        
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
        assert "non-hexadecimal" in output["error"].lower()
    
    def test_fail_empty_input(self):
        """Test FAIL with empty input."""
        exit_code, stdout, stderr = self.run_publichex_verify("")
        
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
        assert "empty" in output["error"].lower()
    
    def test_fail_whitespace_only(self):
        """Test FAIL with whitespace-only input."""
        exit_code, stdout, stderr = self.run_publichex_verify("   \t\n  ")
        
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
        assert "empty" in output["error"].lower()
    
    def test_fail_special_characters(self):
        """Test FAIL with special characters."""
        exit_code, stdout, stderr = self.run_publichex_verify("DEAD@BEEF")
        
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output


class TestPublicHexNormalization:
    """Tests specifically for normalization producing canonical hex."""
    
    def test_normalization_canonical_form(self):
        """Test that normalization produces canonical form."""
        from repeat_hd.cli import normalize_hex
        
        # Various inputs that should all normalize to the same output
        inputs = [
            "48656C6C6F",
            "48656c6c6f",
            "48 65 6C 6C 6F",
            "48\t65\n6C\r6C\n6F",
            "  48656C6C6F  ",
        ]
        
        expected = "48656c6c6f"
        
        for inp in inputs:
            normalized, is_valid, error = normalize_hex(inp)
            assert is_valid, f"Input '{inp}' should be valid"
            assert normalized == expected, f"Input '{inp}' should normalize to '{expected}', got '{normalized}'"


class TestPublicHexPassVectors:
    """Tests for PASS vectors with various whitespace injections."""
    
    def run_publichex_verify(self, hex_input):
        """Helper to run publichex-verify command."""
        cmd = [sys.executable, "-m", "repeat_hd.cli", "publichex-verify", "--hex", hex_input]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout
    
    def test_pass_vector_1(self):
        """Test PASS vector: simple hex."""
        exit_code, stdout = self.run_publichex_verify("AABBCCDD")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "aabbccdd"
    
    def test_pass_vector_1_with_spaces(self):
        """Test PASS vector with spaces injected."""
        exit_code, stdout = self.run_publichex_verify("AA BB CC DD")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "aabbccdd"
    
    def test_pass_vector_2(self):
        """Test PASS vector: longer hex."""
        exit_code, stdout = self.run_publichex_verify("0123456789ABCDEF")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "0123456789abcdef"
    
    def test_pass_vector_2_with_newlines(self):
        """Test PASS vector with newlines injected."""
        exit_code, stdout = self.run_publichex_verify("01234567\n89ABCDEF")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "0123456789abcdef"
    
    def test_pass_vector_3(self):
        """Test PASS vector: all zeros."""
        exit_code, stdout = self.run_publichex_verify("00000000")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "00000000"
    
    def test_pass_vector_3_with_tabs(self):
        """Test PASS vector with tabs injected."""
        exit_code, stdout = self.run_publichex_verify("00\t00\t00\t00")
        assert exit_code == 0
        output = json.loads(stdout)
        assert output["normalized_frame_hex"] == "00000000"


class TestPublicHexFailVectors:
    """Tests for FAIL vectors that should correctly yield FAIL."""
    
    def run_publichex_verify(self, hex_input):
        """Helper to run publichex-verify command."""
        cmd = [sys.executable, "-m", "repeat_hd.cli", "publichex-verify", "--hex", hex_input]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout
    
    def test_fail_vector_odd_length(self):
        """Test FAIL vector: odd length."""
        exit_code, stdout = self.run_publichex_verify("ABC")
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
    
    def test_fail_vector_invalid_char_g(self):
        """Test FAIL vector: contains 'G'."""
        exit_code, stdout = self.run_publichex_verify("ABCDEFG")
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
    
    def test_fail_vector_invalid_char_special(self):
        """Test FAIL vector: contains special character."""
        exit_code, stdout = self.run_publichex_verify("AB-CD")
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
    
    def test_fail_vector_empty(self):
        """Test FAIL vector: empty string."""
        exit_code, stdout = self.run_publichex_verify("")
        assert exit_code == 2
        output = json.loads(stdout)
        assert "error" in output
