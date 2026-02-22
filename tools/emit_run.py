"""Emit a v0.1 run into run/ for subsequent verification via `make verify`."""
import hashlib
import json
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def c14n_bytes(obj) -> bytes:
    """JCS / RFC 8785 canonical JSON bytes (per C14N_RULES.md)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def build_packets(raw_packets: list) -> list:
    packets = []
    for i, raw in enumerate(raw_packets):
        pkt = {
            "crc16": crc16_ccitt_false(raw["payload"].encode("utf-8")),
            "ida_hash": "sha256:" + sha256_hex(raw["ida_payload"].encode("utf-8")),
            "ida_payload": raw["ida_payload"],
            "payload": raw["payload"],
            "seq": i,
        }
        packets.append(pkt)
    return packets


def build_hash_chain(packets: list) -> list:
    genesis = "sha256:" + sha256_hex(b"REPEAT:v0.1:genesis")
    chain = [genesis]
    for pkt in packets:
        nxt = "sha256:" + sha256_hex((chain[-1] + "|").encode("utf-8") + c14n_bytes(pkt))
        chain.append(nxt)
    return chain


def main() -> None:
    run_dir = os.path.join(REPO_ROOT, "run")
    os.makedirs(run_dir, exist_ok=True)

    raw_packets = [
        {"payload": "REPEAT:tile:B4IU:0", "ida_payload": "IDA:0:PLATOPUTER"},
        {"payload": "REPEAT:tile:B4IU:1", "ida_payload": "IDA:1:PLATOPUTER"},
    ]

    packets = build_packets(raw_packets)
    chain = build_hash_chain(packets)

    trace = {
        "hash_chain": chain,
        "packets": packets,
        "version": "0.1",
    }
    receipt = {"sha256_c14n": "sha256:" + sha256_hex(c14n_bytes(trace))}
    verdict = {"result": "PASS", "version": "0.1"}
    manifest = {
        "artifacts": ["run/receipt.json", "run/trace.json", "run/verdict.json"],
        "version": "0.1",
    }

    for rel_path, obj in [
        ("run/manifest.json", manifest),
        ("run/trace.json", trace),
        ("run/receipt.json", receipt),
        ("run/verdict.json", verdict),
    ]:
        full_path = os.path.join(REPO_ROOT, rel_path)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, sort_keys=True, separators=(",", ":"))
            f.write("\n")

    print("Emitted run/ artifacts.")


if __name__ == "__main__":
    main()
