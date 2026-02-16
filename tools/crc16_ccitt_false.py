#!/usr/bin/env python3
"""
CRC-16/CCITT-FALSE implementation.

This module provides a pure Python implementation of CRC-16/CCITT-FALSE
with the following parameters:
- Polynomial: 0x1021
- Initial value: 0xFFFF
- Final XOR: 0x0000
- Reflect input: False
- Reflect output: False

The implementation is designed to mirror standard CRC-16/CCITT-FALSE
behavior and can be used both as a library and as a CLI tool.
"""

import sys
import argparse


def crc16_ccitt_false(data: bytes) -> int:
    """
    Calculate CRC-16/CCITT-FALSE checksum.
    
    Args:
        data: Input bytes to calculate CRC for
        
    Returns:
        CRC-16 checksum as an integer (0x0000 to 0xFFFF)
    """
    crc = 0xFFFF  # Initial value
    poly = 0x1021  # Polynomial
    
    for byte in data:
        crc ^= (byte << 8)  # XOR byte into top of CRC
        
        for _ in range(8):
            if crc & 0x8000:  # If top bit is set
                crc = (crc << 1) ^ poly
            else:
                crc = crc << 1
            crc &= 0xFFFF  # Keep it 16-bit
    
    # Final XOR is 0x0000, so no operation needed
    return crc


def main():
    """Command-line interface for CRC-16/CCITT-FALSE."""
    parser = argparse.ArgumentParser(
        description='Calculate CRC-16/CCITT-FALSE checksum',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate CRC from command line argument
  python3 crc16_ccitt_false.py --payload "test"
  
  # Calculate CRC from stdin
  echo -n "test" | python3 crc16_ccitt_false.py
  
  # Calculate CRC from file via stdin
  cat file.bin | python3 crc16_ccitt_false.py
"""
    )
    
    parser.add_argument(
        '--payload',
        type=str,
        help='Payload string to calculate CRC for (if not provided, reads from stdin)'
    )
    
    args = parser.parse_args()
    
    # Get input data
    if args.payload is not None:
        data = args.payload.encode('utf-8')
    else:
        # Read from stdin.buffer (binary mode)
        data = sys.stdin.buffer.read()
    
    # Calculate CRC
    crc = crc16_ccitt_false(data)
    
    # Print in uppercase, zero-padded hex format
    print(f"{crc:04X}")


if __name__ == '__main__':
    main()
