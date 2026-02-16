"""Unit tests for CRC-16/CCITT-FALSE golden vector validation."""

import unittest
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

from crc16_ccitt_false import crc16_ccitt_false


class TestCRC16GoldenVector(unittest.TestCase):
    """Test CRC-16/CCITT-FALSE with golden vector."""
    
    def test_golden_vector_f0_abc_3_1(self):
        """
        Test that CRC-16/CCITT-FALSE produces the golden vector 0x34B6
        for the payload "F0|ABC|3|1".
        """
        payload = b"F0|ABC|3|1"
        expected_crc = 0x34B6
        
        calculated_crc = crc16_ccitt_false(payload)
        
        self.assertEqual(
            calculated_crc,
            expected_crc,
            f"CRC mismatch: expected 0x{expected_crc:04X}, got 0x{calculated_crc:04X}"
        )


if __name__ == '__main__':
    unittest.main()
