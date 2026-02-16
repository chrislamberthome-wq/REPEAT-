#!/usr/bin/env python3
from __future__ import annotations

import sys
from typing import Optional

def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    poly = 0x1021
    for b in data:
        crc ^= (b << 8) & 0xFFFF
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def main(argv: list[str]) -> int:
    payload: Optional[bytes] = None
    expect: Optional[int] = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--payload":
            i += 1
            if i >= len(argv):
                print("NACK_ARGS (missing --payload value)", file=sys.stderr)
                return 2
            payload = argv[i].encode("utf-8")
        elif a == "--expect":
            i += 1
            if i >= len(argv):
                print("NACK_ARGS (missing --expect value)", file=sys.stderr)
                return 2
            s = argv[i].strip().lower()
            expect = int(s, 16) if s.startswith("0x") else int(s)
        else:
            print(f"NACK_ARGS (unknown arg: {a})", file=sys.stderr)
            return 2
        i += 1

    if payload is None:
        payload = sys.stdin.buffer.read()

    got = crc16_ccitt_false(payload)
    print(f"0x{got:04X}")

    if expect is not None:
        if got == expect:
            print("PASS")
            return 0
        print(f"NACK (got 0x{got:04X}, want 0x{expect:04X})", file=sys.stderr)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
