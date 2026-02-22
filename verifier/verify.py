"""REPEAT v0.1 verifier — fail-closed.

Exit 0 = PASS, non-zero = FAIL.
"""
import hashlib
import json
import os
import re
import sys

RULES_PATH = os.path.join(os.path.dirname(__file__), "rules_v0.1.json")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def c14n_bytes(obj) -> bytes:
    """JCS / RFC 8785: sorted keys, no whitespace, UTF-8 (per C14N_RULES.md)."""
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


def _validate_schema(instance, schema: dict, path: str = "$") -> None:
    """Minimal JSON Schema validation (type/required/additionalProperties/pattern/enum)."""
    typ = schema.get("type")
    if typ == "object":
        if not isinstance(instance, dict):
            _fail(f"Schema: {path} must be object")
        for k in schema.get("required", []):
            if k not in instance:
                _fail(f"Schema: {path}.{k} is required")
        if schema.get("additionalProperties") is False:
            allowed = set(schema.get("properties", {}).keys())
            for k in instance:
                if k not in allowed:
                    _fail(f"Schema: {path}.{k} is not an allowed property")
        for k, sub in schema.get("properties", {}).items():
            if k in instance:
                _validate_schema(instance[k], sub, f"{path}.{k}")
    elif typ == "array":
        if not isinstance(instance, list):
            _fail(f"Schema: {path} must be array")
        items = schema.get("items", {})
        if isinstance(items, dict):
            for i, item in enumerate(instance):
                _validate_schema(item, items, f"{path}[{i}]")
        min_items = schema.get("minItems", 0)
        if len(instance) < min_items:
            _fail(f"Schema: {path} must have >= {min_items} items")
    elif typ == "string":
        if not isinstance(instance, str):
            _fail(f"Schema: {path} must be string")
        pattern = schema.get("pattern")
        if pattern and not re.fullmatch(pattern, instance):
            _fail(f"Schema: {path} value {instance!r} does not match pattern {pattern!r}")
        enum = schema.get("enum")
        if enum is not None and instance not in enum:
            _fail(f"Schema: {path} must be one of {enum}, got {instance!r}")
    elif typ == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            _fail(f"Schema: {path} must be integer")


def _load_json(path: str) -> dict:
    if not os.path.exists(path):
        _fail(f"Missing artifact: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    if not os.path.exists(RULES_PATH):
        _fail(f"Missing rules file: {RULES_PATH}")
    with open(RULES_PATH, encoding="utf-8") as f:
        rules = json.load(f)

    manifest_rel: str = rules["manifest"]
    schemas_map: dict = {k: os.path.join(REPO_ROOT, v) for k, v in rules.get("schemas", {}).items()}

    # Load and validate manifest
    manifest_path = os.path.join(REPO_ROOT, manifest_rel)
    manifest = _load_json(manifest_path)
    schema_path = schemas_map.get(manifest_rel)
    if schema_path:
        _validate_schema(manifest, _load_json(schema_path))

    declared = set(manifest["artifacts"])

    # Check filesystem matches declared set exactly (excluding manifest itself)
    run_dir = os.path.join(REPO_ROOT, "run")
    if not os.path.isdir(run_dir):
        _fail("Missing run/ directory")
    fs_files = {
        os.path.join("run", fname)
        for fname in os.listdir(run_dir)
        if os.path.isfile(os.path.join(run_dir, fname))
    }
    fs_files.discard(manifest_rel)

    if fs_files != declared:
        extra = fs_files - declared
        missing = declared - fs_files
        _fail(f"Manifest/filesystem mismatch. Extra: {extra}, Missing: {missing}")

    # Load and schema-validate all artifacts
    artifacts: dict = {manifest_rel: manifest}
    for rel_path in declared:
        obj = _load_json(os.path.join(REPO_ROOT, rel_path))
        sp = schemas_map.get(rel_path)
        if sp:
            _validate_schema(obj, _load_json(sp))
        artifacts[rel_path] = obj

    # Identify trace, receipt, verdict
    trace_rel = next((k for k in declared if k.endswith("trace.json")), None)
    receipt_rel = next((k for k in declared if k.endswith("receipt.json")), None)
    if trace_rel is None:
        _fail("No trace.json artifact in manifest")
    if receipt_rel is None:
        _fail("No receipt.json artifact in manifest")

    trace = artifacts[trace_rel]
    receipt = artifacts[receipt_rel]

    # Validate hash chain
    packets = trace["packets"]
    chain = trace["hash_chain"]
    if len(chain) != len(packets) + 1:
        _fail(f"hash_chain length {len(chain)} must equal packets count + 1 ({len(packets) + 1})")
    for i, pkt in enumerate(packets):
        pkt_bytes = c14n_bytes(pkt)
        expected = "sha256:" + sha256_hex((chain[i] + "|").encode("utf-8") + pkt_bytes)
        if chain[i + 1] != expected:
            _fail(f"Hash chain break at packet {i}: expected {expected}, got {chain[i + 1]}")

    # Validate CRC16 and IDA hash for each packet
    for i, pkt in enumerate(packets):
        expected_crc = crc16_ccitt_false(pkt["payload"].encode("utf-8"))
        if pkt["crc16"] != expected_crc:
            _fail(f"CRC16 mismatch at packet {i}: expected {expected_crc}, got {pkt['crc16']}")
        expected_ida = "sha256:" + sha256_hex(pkt["ida_payload"].encode("utf-8"))
        if pkt["ida_hash"] != expected_ida:
            _fail(f"IDA hash mismatch at packet {i}: expected {expected_ida}, got {pkt['ida_hash']}")

    # Validate receipt (sha256 of canonical trace)
    expected_digest = "sha256:" + sha256_hex(c14n_bytes(trace))
    if receipt["sha256_c14n"] != expected_digest:
        _fail(f"Receipt mismatch: expected {expected_digest}, got {receipt['sha256_c14n']}")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
