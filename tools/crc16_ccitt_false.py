#!/usr/bin/env python3
"""
Reference implementation of CRC-16/CCITT-FALSE.

Algorithm Parameters:
- Polynomial: 0x1021
- Initial Value: 0xFFFF
- XOROUT: 0x0000
- Reflection: None (no input/output reflection)

This implementation ensures deterministic, reproducible CRC calculation
across all platforms and Python versions.
"""

# Algorithm constants - FROZEN, DO NOT MODIFY
POLY = 0x1021
INIT = 0xFFFF
XOROUT = 0x0000


def crc16_ccitt_false(data: bytes) -> int:
    """
    Calculate CRC-16/CCITT-FALSE checksum.
    
    Args:
        data: Input bytes to calculate CRC for
        
    Returns:
        16-bit CRC value (0x0000 - 0xFFFF)
        
    Examples:
        >>> crc16_ccitt_false(b"")
        65535
        >>> hex(crc16_ccitt_false(b"123456789"))
        '0x29b1'
        >>> hex(crc16_ccitt_false(b"ABC"))
        '0xf508'
    """
    crc = INIT
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLY
            else:
                crc = crc << 1
            crc &= 0xFFFF  # Keep it 16-bit
    
    return crc ^ XOROUT


def crc16_ccitt_false_str(text: str, encoding: str = 'utf-8') -> int:
    """
    Calculate CRC-16/CCITT-FALSE for a string.
    
    Args:
        text: Input string
        encoding: Character encoding to use (default: 'utf-8')
        
    Returns:
        16-bit CRC value
        
    Examples:
        >>> hex(crc16_ccitt_false_str("123456789"))
        '0x29b1'
        >>> hex(crc16_ccitt_false_str("ABC"))
        '0xf508'
    """
    return crc16_ccitt_false(text.encode(encoding))


if __name__ == "__main__":
    import sys
    
    # Simple CLI for testing
    if len(sys.argv) > 1:
        text = sys.argv[1]
        crc = crc16_ccitt_false_str(text)
        print(f"0x{crc:04X}")
    else:
        # Run basic verification
        test_vectors = [
            (b"", 0xFFFF),
            (b"123456789", 0x29B1),
            (b"ABC", 0xF508),
        ]
        
        print("CRC-16/CCITT-FALSE Reference Implementation")
        print("=" * 50)
        for data, expected in test_vectors:
            result = crc16_ccitt_false(data)
            status = "✓" if result == expected else "✗"
            print(f"{status} Input: {data!r:20s} CRC: 0x{result:04X} (expected: 0x{expected:04X})")
