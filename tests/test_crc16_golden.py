"""Golden vector tests for CRC-16 CCITT-False implementation."""

import unittest
import sys
import os

# Add tools directory to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from crc16_ccitt_false import crc16_ccitt_false


class TestCrc16Golden(unittest.TestCase):
    """Test CRC-16 CCITT-False against golden test vectors."""
    
    def test_empty_string(self):
        """Test CRC-16 of empty string."""
        data = b""
        result = crc16_ccitt_false(data)
        # CRC-16 CCITT-False of empty data is 0xFFFF (initial value)
        self.assertEqual(result, 0xFFFF)
    
    def test_single_byte_zero(self):
        """Test CRC-16 of single null byte."""
        data = b"\x00"
        result = crc16_ccitt_false(data)
        # Known value for single 0x00 byte
        self.assertEqual(result, 0xE1F0)
    
    def test_single_byte_0x31(self):
        """Test CRC-16 of ASCII '1'."""
        data = b"1"
        result = crc16_ccitt_false(data)
        # Known value for ASCII '1' (0x31)
        self.assertEqual(result, 0xC782)
    
    def test_hello_world(self):
        """Test CRC-16 of 'Hello, World!'."""
        data = b"Hello, World!"
        result = crc16_ccitt_false(data)
        # Known CRC-16 CCITT-False value
        self.assertEqual(result, 0x67DA)
    
    def test_primary_golden_vector(self):
        """Test the primary golden vector from documentation."""
        data = b"F0|ABC|3|1"
        result = crc16_ccitt_false(data)
        # Expected value as documented in CRC16_REPRO.md
        self.assertEqual(result, 0x34B6)
    
    def test_numeric_sequence(self):
        """Test CRC-16 of numeric sequence."""
        data = b"123456789"
        result = crc16_ccitt_false(data)
        # Well-known test vector for CRC-16 CCITT-False
        self.assertEqual(result, 0x29B1)
    
    def test_all_zeros(self):
        """Test CRC-16 of multiple zero bytes."""
        data = b"\x00\x00\x00\x00"
        result = crc16_ccitt_false(data)
        # CRC of 4 null bytes
        self.assertEqual(result, 0x84C0)
    
    def test_all_ones(self):
        """Test CRC-16 of all 0xFF bytes."""
        data = b"\xFF\xFF\xFF\xFF"
        result = crc16_ccitt_false(data)
        # CRC of 4 bytes of 0xFF
        self.assertEqual(result, 0x1D0F)
    
    def test_alternating_pattern(self):
        """Test CRC-16 with alternating bit pattern."""
        data = b"\xAA\x55\xAA\x55"
        result = crc16_ccitt_false(data)
        # CRC of alternating 0xAA and 0x55
        self.assertEqual(result, 0x4BC6)


if __name__ == "__main__":
    unittest.main()
