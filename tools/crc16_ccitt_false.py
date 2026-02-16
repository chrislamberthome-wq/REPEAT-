"""
CRC-16/CCITT-FALSE implementation.

This module provides a Python implementation of the CRC-16/CCITT-FALSE algorithm.
Parameters:
    - Polynomial: 0x1021
    - Initial value: 0xFFFF
    - Input reflected: False
    - Output reflected: False
    - XOR out: 0x0000
"""


def crc16_ccitt_false(data: bytes) -> int:
    """
    Calculate CRC-16/CCITT-FALSE checksum for the given data.
    
    Args:
        data: Input data as bytes
        
    Returns:
        16-bit CRC checksum as integer
    """
    crc = 0xFFFF  # Initial value
    poly = 0x1021  # Polynomial
    
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ poly
            else:
                crc = crc << 1
            crc &= 0xFFFF  # Keep it 16-bit
    
    return crc


def crc16_ccitt_false_hex(data: bytes) -> str:
    """
    Calculate CRC-16/CCITT-FALSE checksum and return as hex string.
    
    Args:
        data: Input data as bytes
        
    Returns:
        16-bit CRC checksum as hex string (e.g., "1234")
    """
    return f"{crc16_ccitt_false(data):04X}"
