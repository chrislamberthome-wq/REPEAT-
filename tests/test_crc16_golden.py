"""
Golden vector tests for CRC-16/CCITT-FALSE.

This test suite verifies the reference implementation against frozen golden
vectors to ensure deterministic, reproducible behavior across platforms.

Test vectors are immutable and MUST NOT be changed without formal review.
"""

import pytest
from tools.crc16_ccitt_false import crc16_ccitt_false, crc16_ccitt_false_str


class TestCRC16GoldenVectors:
    """Test CRC-16/CCITT-FALSE against frozen golden vectors."""
    
    def test_empty_string(self):
        """Test CRC of empty byte sequence."""
        # Empty input should produce INIT value XOR XOROUT = 0xFFFF ^ 0x0000
        result = crc16_ccitt_false(b"")
        expected = 0xFFFF
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
    
    def test_numeric_string_123456789(self):
        """Test CRC of '123456789' - standard test vector."""
        # This is a well-known test vector for CRC-16/CCITT-FALSE
        result = crc16_ccitt_false(b"123456789")
        expected = 0x29B1
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
    
    def test_text_abc(self):
        """Test CRC of 'ABC'."""
        result = crc16_ccitt_false(b"ABC")
        expected = 0xF508
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
    
    def test_binary_sequence_00_to_09(self):
        """Test CRC of binary sequence 0x00 through 0x09."""
        data = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09])
        result = crc16_ccitt_false(data)
        expected = 0xC241
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
    
    def test_binary_ff_repeated_32_times(self):
        """Test CRC of 0xFF repeated 32 times."""
        data = bytes([0xFF] * 32)
        result = crc16_ccitt_false(data)
        expected = 0x75F8
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
    
    def test_binary_all_bytes_00_to_ff(self):
        """Test CRC of all byte values from 0x00 to 0xFF (256 bytes)."""
        data = bytes(range(256))
        result = crc16_ccitt_false(data)
        expected = 0x3FBD
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"


class TestCRC16StringEncoding:
    """Test string encoding behavior for UTF-8."""
    
    def test_ascii_string(self):
        """Test that ASCII strings are encoded correctly."""
        # Using string wrapper should match byte-level calculation
        result_str = crc16_ccitt_false_str("ABC")
        result_bytes = crc16_ccitt_false(b"ABC")
        assert result_str == result_bytes
        assert result_str == 0xF508
    
    def test_utf8_encoding(self):
        """Test UTF-8 encoding of non-ASCII characters."""
        # Test a simple UTF-8 character
        text = "é"  # U+00E9, UTF-8: 0xC3 0xA9
        result = crc16_ccitt_false_str(text, encoding='utf-8')
        # Verify it's calculated on the UTF-8 bytes
        expected = crc16_ccitt_false(b"\xc3\xa9")
        assert result == expected


class TestCRC16Determinism:
    """Test deterministic behavior across invocations."""
    
    def test_repeated_calculation_same_result(self):
        """Ensure repeated calculations produce identical results."""
        data = b"test data for determinism check"
        results = [crc16_ccitt_false(data) for _ in range(10)]
        assert len(set(results)) == 1, "CRC calculation is not deterministic!"
    
    def test_order_independence(self):
        """Test that calculation order doesn't affect results."""
        # Calculate CRCs for different inputs
        inputs = [b"first", b"second", b"third"]
        
        # Forward order
        forward = [crc16_ccitt_false(data) for data in inputs]
        
        # Reverse order
        reverse = [crc16_ccitt_false(data) for data in reversed(inputs)]
        reverse.reverse()
        
        assert forward == reverse, "Calculation order affected results!"


class TestCRC16EdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_byte_zero(self):
        """Test CRC of a single zero byte."""
        result = crc16_ccitt_false(b"\x00")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF
    
    def test_single_byte_ff(self):
        """Test CRC of a single 0xFF byte."""
        result = crc16_ccitt_false(b"\xFF")
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF
    
    def test_large_input(self):
        """Test CRC calculation on larger input (1KB)."""
        data = bytes(range(256)) * 4  # 1024 bytes
        result = crc16_ccitt_false(data)
        assert isinstance(result, int)
        assert 0 <= result <= 0xFFFF


class TestCRC16GoldenVectorsParameterized:
    """Parametrized golden vector tests for concise verification."""
    
    @pytest.mark.parametrize("data,expected", [
        (b"", 0xFFFF),
        (b"123456789", 0x29B1),
        (b"ABC", 0xF508),
        (bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]), 0xC241),
        (bytes([0xFF] * 32), 0x75F8),
        (bytes(range(256)), 0x3FBD),
    ])
    def test_golden_vector(self, data, expected):
        """Verify golden vector matches expected CRC."""
        result = crc16_ccitt_false(data)
        assert result == expected, f"Expected 0x{expected:04X}, got 0x{result:04X}"
