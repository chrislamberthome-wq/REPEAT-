"""
Test CRC-16/CCITT-FALSE CLI parity.

This test verifies the command-line interface behavior to prevent
future CLI syntax changes and ensure consistent stdin/argument handling.
"""

import unittest
import subprocess
import sys


class TestCRC16CLIParity(unittest.TestCase):
    """Test CLI behavior for CRC-16/CCITT-FALSE tool."""
    
    def test_cli_with_payload_argument(self):
        """Test CRC calculation with --payload argument."""
        result = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py', '--payload', 'F0|ABC|3|1'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, "CLI should exit successfully")
        output = result.stdout.strip()
        self.assertEqual(output, '34B6', f"Expected 34B6, got {output}")
    
    def test_cli_with_stdin_input(self):
        """Test CRC calculation via stdin."""
        result = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py'],
            input=b'F0|ABC|3|1',
            capture_output=True
        )
        
        self.assertEqual(result.returncode, 0, "CLI should exit successfully")
        output = result.stdout.decode().strip()
        self.assertEqual(output, '34B6', f"Expected 34B6, got {output}")
    
    def test_cli_stdin_parity(self):
        """
        Test that stdin and --payload produce identical output.
        
        This ensures consistency between different input methods.
        """
        test_data = 'test123'
        
        # Test with --payload
        result1 = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py', '--payload', test_data],
            capture_output=True,
            text=True
        )
        
        # Test with stdin
        result2 = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py'],
            input=test_data.encode(),
            capture_output=True
        )
        
        output1 = result1.stdout.strip()
        output2 = result2.stdout.decode().strip()
        
        self.assertEqual(
            output1,
            output2,
            f"stdin and --payload should produce identical output: {output1} vs {output2}"
        )
    
    def test_cli_output_format(self):
        """
        Test that output is uppercase, zero-padded hex format.
        
        This verifies the format specification is maintained.
        """
        result = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py', '--payload', 'test'],
            capture_output=True,
            text=True
        )
        
        output = result.stdout.strip()
        
        # Should be 4 characters (zero-padded to 4 hex digits)
        self.assertEqual(len(output), 4, f"Output should be 4 hex digits, got: {output}")
        
        # Should be uppercase
        self.assertEqual(output, output.upper(), f"Output should be uppercase, got: {output}")
        
        # Should be valid hex
        try:
            int(output, 16)
        except ValueError:
            self.fail(f"Output should be valid hex, got: {output}")
    
    def test_cli_empty_input(self):
        """Test CRC calculation with empty input."""
        result = subprocess.run(
            [sys.executable, 'tools/crc16_ccitt_false.py', '--payload', ''],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, "CLI should handle empty input")
        output = result.stdout.strip()
        self.assertEqual(len(output), 4, "Output should still be 4 hex digits")
        # Empty input with CRC-16/CCITT-FALSE should give FFFF
        self.assertEqual(output, 'FFFF', f"Empty input should give FFFF, got {output}")


if __name__ == '__main__':
    unittest.main()
