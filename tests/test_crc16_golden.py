"""
Test CRC-16/CCITT-FALSE golden vector.

This test validates that the CRC-16/CCITT-FALSE implementation
correctly reproduces the golden vector.
"""

import unittest
from tools.crc16_ccitt_false import crc16_ccitt_false


class TestCRC16Golden(unittest.TestCase):
    """Test golden vector for CRC-16/CCITT-FALSE."""
    
    def test_golden_vector(self):
        """
        Test that the golden vector F0|ABC|3|1 produces CRC 0x34B6.
        
        This is the reference golden vector that validates the
        CRC-16/CCITT-FALSE implementation is correct.
        """
        # Golden vector: F0|ABC|3|1 (ASCII string) -> 0x34B6
        payload = b'F0|ABC|3|1'
        expected_crc = 0x34B6
        
        calculated_crc = crc16_ccitt_false(payload)
        
        self.assertEqual(
            calculated_crc,
            expected_crc,
            f"CRC mismatch: expected {expected_crc:04X}, got {calculated_crc:04X}"
        )


if __name__ == '__main__':
    unittest.main()
