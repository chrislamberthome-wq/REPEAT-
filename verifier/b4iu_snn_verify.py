#!/usr/bin/env python3
"""B4IU-SNN v0.1 conformance verifier.  FAIL-CLOSED.

Usage: python -m verifier.b4iu_snn_verify <run_dir>
Exits 0 and prints PASS on success; exits 1 and prints FAIL: … on any error.
"""

import hashlib
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"
GENESIS_HASH = "sha256:" + "0" * 64
REQUIRED_ARTIFACTS = {"manifest.json", "policy.json", "trace.jsonl", "receipt.json", "verdict.json"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _c14n(obj) -> bytes:
    """JCS (RFC 8785) canonical JSON: UTF-8, sorted keys, no insignificant whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _load_schema(name: str) -> dict:
    with open(SCHEMA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def _load_json(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _validate(instance: dict, schema: dict, label: str) -> None:
    v = Draft202012Validator(schema)
    errors = sorted(v.iter_errors(instance), key=lambda e: list(e.absolute_path))
    if errors:
        _fail(f"{label} schema invalid: {errors[0].message}")


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main verifier
# ---------------------------------------------------------------------------

def verify(run_dir: str) -> None:
    run_path = Path(run_dir)

    # 1. Required artifacts exist
    for art in REQUIRED_ARTIFACTS:
        if not (run_path / art).exists():
            _fail(f"Missing required artifact: {art}")

    # 2. Manifest — load & validate schema
    manifest_schema = _load_schema("b4iu_snn_manifest.schema.json")
    manifest = _load_json(run_path / "manifest.json")
    _validate(manifest, manifest_schema, "manifest.json")

    run_id = manifest["run_id"]

    # 3. manifest.artifacts must exactly match actual top-level files
    declared = manifest["artifacts"]
    if len(declared) != len(set(declared)):
        _fail("manifest.artifacts contains duplicate entries")
    actual_files = {f.name for f in run_path.iterdir() if f.is_file()}
    if set(declared) != actual_files:
        _fail(
            f"manifest.artifacts mismatch: "
            f"declared={sorted(declared)}, actual={sorted(actual_files)}"
        )

    # 4. Policy — load & validate schema
    policy_schema = _load_schema("b4iu_snn_policy.schema.json")
    policy = _load_json(run_path / "policy.json")
    _validate(policy, policy_schema, "policy.json")

    H_max = policy["H_max"]
    locality_event_types = set(policy["locality_event_types"])
    hop_exceptions = set(policy["hop_exceptions"])

    # 5. Trace — parse, no blank lines, seq 0..N-1, prev_hash chain, schema validity
    trace_event_schema = _load_schema("b4iu_snn_trace_event.schema.json")
    trace_events = []

    with open(run_path / "trace.jsonl", encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            if raw.strip() == "":
                _fail(f"trace.jsonl: blank line at line {lineno}")
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                _fail(f"trace.jsonl: invalid JSON at line {lineno}: {exc}")
            trace_events.append(event)

    if not trace_events:
        _fail("trace.jsonl: empty")

    prev_hash = GENESIS_HASH
    for i, event in enumerate(trace_events):
        _validate(event, trace_event_schema, f"trace.jsonl event seq={i}")

        if event["seq"] != i:
            _fail(f"trace.jsonl: seq mismatch at index {i}: expected {i}, got {event['seq']}")

        if event["prev_hash"] != prev_hash:
            _fail(f"trace.jsonl: prev_hash mismatch at seq={i}")

        # hash = sha256(c14n(event_without_hash))
        event_without_hash = {k: v for k, v in event.items() if k != "hash"}
        expected_hash = _sha256(_c14n(event_without_hash))
        if event["hash"] != expected_hash:
            _fail(f"trace.jsonl: hash mismatch at seq={i}")

        prev_hash = event["hash"]

    trace_root = trace_events[-1]["hash"]

    # 6. Step structure: STEP_START/STEP_END balanced, steps nondecreasing
    open_steps = {}
    last_step = -1
    for event in trace_events:
        step = event.get("step")
        if step is not None:
            if step < last_step:
                _fail(f"trace.jsonl: step not nondecreasing at seq={event['seq']}")
            last_step = step

        et = event.get("event_type", "")
        if et == "STEP_START":
            if step in open_steps:
                _fail(f"trace.jsonl: STEP_START for step={step} already open at seq={event['seq']}")
            open_steps[step] = event.get("unit_id")
        elif et == "STEP_END":
            if step not in open_steps:
                _fail(f"trace.jsonl: STEP_END for step={step} without STEP_START at seq={event['seq']}")
            del open_steps[step]

    if open_steps:
        _fail(f"trace.jsonl: unclosed steps: {sorted(open_steps.keys())}")

    # 7. Locality policy
    for event in trace_events:
        et = event.get("event_type", "")
        if et not in locality_event_types:
            continue
        hop_count = event.get("hop_count")
        if hop_count is None:
            _fail(f"trace.jsonl: locality event seq={event['seq']} missing hop_count")

        unit_id = event.get("unit_id", "")
        exception_reason = event.get("exception_reason")

        if hop_count > H_max:
            if unit_id not in hop_exceptions:
                _fail(
                    f"trace.jsonl: hop_count={hop_count} > H_max={H_max} at seq={event['seq']}"
                    f" (no exception for unit_id={unit_id!r})"
                )
        else:
            # hop ≤ H_max: exception_reason MUST be null
            if exception_reason is not None:
                _fail(
                    f"trace.jsonl: exception_reason must be null when hop_count <= H_max"
                    f" at seq={event['seq']}"
                )

    # 8. IDA root — enforce consistency, then hash sorted unique units
    units = {}
    for event in trace_events:
        uid = event.get("unit_id")
        if not uid:
            continue
        entry = {"unit_id": uid}
        if uid in units:
            if units[uid] != entry:
                _fail(f"trace.jsonl: inconsistent IDA fields for unit_id={uid!r}")
        else:
            units[uid] = entry

    unique_units = sorted(units.values(), key=lambda u: u["unit_id"])
    ida_root = _sha256(_c14n(unique_units))

    # 9. Recompute receipt and compare byte-for-byte (canonical form)
    receipt_body = {
        "schema": "b4iu_snn_receipt_v0.1",
        "run_id": run_id,
        "trace_root": trace_root,
        "ida_root": ida_root,
    }
    receipt_recomputed = dict(receipt_body)
    receipt_recomputed["sha256_c14n"] = _sha256(_c14n(receipt_body))

    receipt_schema = _load_schema("b4iu_snn_receipt.schema.json")
    receipt_actual = _load_json(run_path / "receipt.json")
    _validate(receipt_actual, receipt_schema, "receipt.json")

    if _c14n(receipt_actual) != _c14n(receipt_recomputed):
        _fail(
            f"receipt.json does not match recomputed receipt\n"
            f"  actual:     {_c14n(receipt_actual).decode()}\n"
            f"  recomputed: {_c14n(receipt_recomputed).decode()}"
        )

    # 10. Verdict — schema-valid and verdict must be PASS
    verdict_schema = _load_schema("b4iu_snn_verdict.schema.json")
    verdict = _load_json(run_path / "verdict.json")
    _validate(verdict, verdict_schema, "verdict.json")

    if verdict.get("verdict") != "PASS":
        _fail(f"verdict is not PASS: {verdict.get('verdict')!r}")

    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(
            "Usage: python -m verifier.b4iu_snn_verify <run_dir>",
            file=sys.stderr,
        )
        sys.exit(1)
    verify(sys.argv[1])
