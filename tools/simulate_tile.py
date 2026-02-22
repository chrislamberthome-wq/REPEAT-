"""Simulate a single B4IU tile and print its canonical packet JSON."""
import hashlib
import json
import sys


def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly=0x1021, init=0xFFFF, refin=False, refout=False, xorout=0."""
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


def simulate_tile(seq: int, payload: str, ida_payload: str) -> dict:
    """Return a B4IU tile packet dict with CRC16 and IDA hash computed."""
    return {
        "crc16": crc16_ccitt_false(payload.encode("utf-8")),
        "ida_hash": "sha256:" + hashlib.sha256(ida_payload.encode("utf-8")).hexdigest(),
        "ida_payload": ida_payload,
        "payload": payload,
        "seq": seq,
    }


def main() -> None:
    seq = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    payload = sys.argv[2] if len(sys.argv) > 2 else f"REPEAT:tile:B4IU:{seq}"
    ida_payload = sys.argv[3] if len(sys.argv) > 3 else f"IDA:{seq}:PLATOPUTER"
    pkt = simulate_tile(seq, payload, ida_payload)
    print(json.dumps(pkt, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
