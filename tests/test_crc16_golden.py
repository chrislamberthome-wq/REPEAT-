import unittest
from tools.crc16_ccitt_false import crc16_ccitt_false

class TestCrc16Golden(unittest.TestCase):
    def test_golden_vector(self):
        self.assertEqual(crc16_ccitt_false(b"F0|ABC|3|1"), 0x34B6)

if __name__ == "__main__":
    unittest.main()
