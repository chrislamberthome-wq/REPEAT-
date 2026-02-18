#!/usr/bin/env python3
"""
CRC-16/CCITT-FALSE implementation.

Algorithm parameters:
- poly=0x1021
- init=0xFFFF
- refin=false (no input reflection)
- refout=false (no output reflection)
- xorout=0x0000 (no final XOR)

This implementation validates the golden vector:
  Input:  "F0|ABC|3|1"
  Output: 0x34B6
"""

import sys
import argparse


def crc16_ccitt_false(data: bytes) -> int:
    """
    Calculate CRC-16/CCITT-FALSE for the given data.
    
    Args:
        data: Input bytes to calculate CRC for
        
    Returns:
        16-bit CRC value
    """
    crc = 0xFFFF  # init value
    poly = 0x1021  # polynomial
    
    for byte in data:
        crc ^= (byte << 8)  # XOR byte into MSB of crc
        
        for _ in range(8):
            if crc & 0x8000:  # if MSB is set
                crc = (crc << 1) ^ poly
            else:
                crc = crc << 1
            crc &= 0xFFFF  # keep it 16-bit
    
    # xorout = 0x0000, so no final XOR needed
    return crc


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Calculate CRC-16/CCITT-FALSE checksum'
    )
    parser.add_argument(
        '--payload',
        type=str,
        help='Payload string to calculate CRC for'
    )
    parser.add_argument(
        '--expect',
        type=str,
        help='Expected CRC value in hex (e.g., 0x34B6) for validation'
    )
    
    args = parser.parse_args()
    
    # Get input data
    if args.payload:
        data = args.payload.encode('utf-8')
    else:
        # Read from stdin
        data = sys.stdin.buffer.read()
    
    # Calculate CRC
    crc = crc16_ccitt_false(data)
    
    # Validation mode
    if args.expect:
        try:
            # Parse expected value (supports 0x34B6 or 34B6)
            expected = int(args.expect, 16)
            if crc == expected:
                print(f"PASS: CRC matches expected value 0x{expected:04X}")
                sys.exit(0)
            else:
                print(f"NACK: CRC mismatch. Expected 0x{expected:04X}, got 0x{crc:04X}")
                sys.exit(1)
        except ValueError as e:
            print(f"Error: Invalid expected value '{args.expect}': {e}", file=sys.stderr)
            sys.exit(2)
    else:
        # Print mode
        print(f"0x{crc:04X}")
        sys.exit(0)


if __name__ == '__main__':
    main()
