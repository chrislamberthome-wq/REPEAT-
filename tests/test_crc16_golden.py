"""
Golden vector validation tests for CRC-16/CCITT-FALSE implementation.

This test suite validates the CRC-16/CCITT-FALSE implementation against
known golden vectors to ensure correctness.
"""

import unittest
from tools.crc16_ccitt_false import crc16_ccitt_false, crc16_ccitt_false_hex


class TestCRC16GoldenVectors(unittest.TestCase):
    """Test CRC-16/CCITT-FALSE implementation against golden vectors."""

    def test_empty_string(self):
        """Test CRC of empty data."""
        data = b""
        expected = 0xFFFF
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected, 
                        f"CRC of empty data should be 0xFFFF, got 0x{result:04X}")

    def test_single_zero_byte(self):
        """Test CRC of single zero byte."""
        data = b"\x00"
        expected = 0xE1F0
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of 0x00 should be 0xE1F0, got 0x{result:04X}")

    def test_ascii_123456789(self):
        """Test CRC of ASCII string '123456789'."""
        data = b"123456789"
        expected = 0x29B1
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of '123456789' should be 0x29B1, got 0x{result:04X}")

    def test_ascii_hello_world(self):
        """Test CRC of 'Hello, World!' string."""
        data = b"Hello, World!"
        # This is a calculated golden vector for CCITT-FALSE
        expected = 0x67DA
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of 'Hello, World!' should be 0x67DA, got 0x{result:04X}")

    def test_all_zeros(self):
        """Test CRC of multiple zero bytes."""
        data = b"\x00\x00\x00\x00"
        expected = 0x84C0
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of four zero bytes should be 0x84C0, got 0x{result:04X}")

    def test_all_ones(self):
        """Test CRC of multiple 0xFF bytes."""
        data = b"\xFF\xFF\xFF\xFF"
        expected = 0x1D0F
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of four 0xFF bytes should be 0x1D0F, got 0x{result:04X}")

    def test_hex_output(self):
        """Test hex string output format."""
        data = b"123456789"
        expected = "29B1"
        result = crc16_ccitt_false_hex(data)
        self.assertEqual(result, expected,
                        f"Hex CRC of '123456789' should be '29B1', got '{result}'")

    def test_incremental_sequence(self):
        """Test CRC of incremental byte sequence."""
        data = bytes(range(256))
        expected = 0x3FBD  # Calculated for 0x00..0xFF
        result = crc16_ccitt_false(data)
        self.assertEqual(result, expected,
                        f"CRC of 0-255 sequence should be 0x3FBD, got 0x{result:04X}")


if __name__ == '__main__':
    unittest.main()
