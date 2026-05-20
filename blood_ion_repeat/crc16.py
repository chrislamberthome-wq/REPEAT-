"""CRC-16/CCITT-FALSE implementation (poly=0x1021, init=0xFFFF, refin=False, refout=False, xorout=0x0000)."""
from __future__ import annotations

_POLY = 0x1021
_INIT = 0xFFFF


def crc16_ccitt_false(data: bytes) -> int:
    """Return the CRC-16/CCITT-FALSE checksum for *data*."""
    crc = _INIT
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ _POLY
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def crc16_hex(data: bytes) -> str:
    """Return the checksum as a zero-padded 4-character hex string."""
    return f"{crc16_ccitt_false(data):04X}"
