"""CLI parity tests for CRC-16 CCITT-False implementation.

This test verifies that the CLI tool produces identical results when
receiving input via stdin versus functional invocation, ensuring
consistency across different usage patterns.
"""

import subprocess
import sys
import unittest


class TestCrc16CliParity(unittest.TestCase):
    """Test CLI stdin input works identically to functional invocation."""
    
    def test_cli_stdin(self):
        """Test CLI with stdin input produces expected output."""
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=b"F0|ABC|3|1",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        out = p.stdout.decode("utf-8").strip().splitlines()[0]
        self.assertEqual(out, "0x34B6")
    
    def test_cli_argument(self):
        """Test CLI with command-line argument produces expected output."""
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py", "F0|ABC|3|1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        out = p.stdout.decode("utf-8").strip().splitlines()[0]
        self.assertEqual(out, "0x34B6")
    
    def test_cli_stdin_vs_argument_parity(self):
        """Test that stdin and argument methods produce identical output."""
        # Run with stdin
        p1 = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=b"F0|ABC|3|1",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        stdin_out = p1.stdout.decode("utf-8").strip()
        
        # Run with argument
        p2 = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py", "F0|ABC|3|1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        arg_out = p2.stdout.decode("utf-8").strip()
        
        # Both should produce identical output
        self.assertEqual(stdin_out, arg_out)
    
    def test_cli_empty_stdin(self):
        """Test CLI with empty stdin input."""
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        out = p.stdout.decode("utf-8").strip().splitlines()[0]
        # Empty string should produce 0xFFFF (initial value)
        self.assertEqual(out, "0xFFFF")
    
    def test_cli_multiline_stdin(self):
        """Test CLI handles multiline input correctly."""
        test_data = b"line1\nline2\nline3"
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=test_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        out = p.stdout.decode("utf-8").strip().splitlines()[0]
        # Should process entire input including newlines
        self.assertIsNotNone(out)
        self.assertTrue(out.startswith("0x"))
    
    def test_cli_binary_data_stdin(self):
        """Test CLI handles binary data correctly via stdin."""
        test_data = b"\x00\x01\x02\x03\xFF"
        p = subprocess.run(
            [sys.executable, "tools/crc16_ccitt_false.py"],
            input=test_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        out = p.stdout.decode("utf-8").strip().splitlines()[0]
        # Should produce valid hex output
        self.assertIsNotNone(out)
        self.assertTrue(out.startswith("0x"))
        # Verify it's a valid 4-digit hex number
        self.assertEqual(len(out), 6)  # "0x" + 4 hex digits


if __name__ == "__main__":
    unittest.main()
