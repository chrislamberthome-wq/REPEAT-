#!/usr/bin/env python3
"""
CRC-16 CCITT-False calculator for auditor-facing CLI verification.

This tool computes CRC-16 using the CCITT-False polynomial (0x1021) with:
- Initial value: 0xFFFF
- No reflection
- No final XOR

Usage:
    # From stdin
    printf "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
    
    # From command-line argument
    python3 tools/crc16_ccitt_false.py "F0|ABC|3|1"
"""

import sys


def crc16_ccitt_false(data: bytes) -> int:
    """
    Calculate CRC-16 CCITT-False.
    
    Polynomial: 0x1021
    Initial value: 0xFFFF
    Input reflection: No
    Output reflection: No
    Final XOR: 0x0000
    
    Args:
        data: Input bytes to compute CRC over
        
    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF
    poly = 0x1021
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc = crc << 1
            crc &= 0xFFFF
    
    return crc


def main():
    """Main entry point for CLI."""
    if len(sys.argv) > 1:
        # Read from command-line argument
        data = sys.argv[1].encode('utf-8')
    else:
        # Read from stdin (binary mode to avoid platform-specific line ending issues)
        data = sys.stdin.buffer.read()
    
    crc = crc16_ccitt_false(data)
    print(f"0x{crc:04X}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
