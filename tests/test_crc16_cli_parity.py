import subprocess
import sys
import unittest

class TestCrc16CliParity(unittest.TestCase):
    def test_cli_stdin(self):
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=b"F0|ABC|3|1",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        first = p.stdout.decode("utf-8").strip().splitlines()[0]
        self.assertEqual(first, "0x34B6")

if __name__ == "__main__":
    unittest.main()
