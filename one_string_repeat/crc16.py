"""
crc16.py — CRC-16/CCITT-FALSE checksum for one_string_REPEAT v1.0.

Algorithm parameters:
    Width:   16
    Poly:    0x1021
    Init:    0xFFFF
    RefIn:   False
    RefOut:  False
    XorOut:  0x0000
"""
from __future__ import annotations


def crc16_ccitt_false(data: bytes) -> int:
    """
    Compute the CRC-16/CCITT-FALSE checksum of *data*.

    Returns a 16-bit unsigned integer.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"crc16_ccitt_false requires bytes, got {type(data).__name__}")
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def crc16_hex(data: bytes) -> str:
    """
    Return CRC-16/CCITT-FALSE of *data* as an upper-case 4-character hex string.

    Example: ``'A12F'``
    """
    return f"{crc16_ccitt_false(data):04X}"
