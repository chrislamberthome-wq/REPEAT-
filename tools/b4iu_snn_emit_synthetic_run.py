#!/usr/bin/env python3
"""Emit a synthetic B4IU-SNN v0.1 run directory for conformance testing.

Usage: python -m tools.b4iu_snn_emit_synthetic_run <run_dir>
"""

import hashlib
import json
import os
import sys

GENESIS_HASH = "sha256:" + "0" * 64
POLICY_VERSION = "b4iu_snn_policy_v0.1"
_T_BASE_NS = 1_700_000_000_000_000_000  # fixed base for deterministic timestamps


def _c14n(obj) -> bytes:
    """JCS (RFC 8785) canonical JSON: UTF-8, sorted keys, no insignificant whitespace."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _event_hash(event: dict) -> str:
    """hash = sha256(c14n(event_without_hash))  — spec §trace-hashchain."""
    event_without_hash = {k: v for k, v in event.items() if k != "hash"}
    return _sha256(_c14n(event_without_hash))


def emit(run_dir: str) -> None:
    os.makedirs(run_dir, exist_ok=True)

    # Remove .gitkeep placeholder if present (emitting real artifacts supersedes it)
    gitkeep = os.path.join(run_dir, ".gitkeep")
    if os.path.exists(gitkeep):
        os.remove(gitkeep)

    run_id = "b4iu_snn_synthetic_run_v0.1"

    # ------------------------------------------------------------------ trace
    events = []

    def _append(seq: int, event_type: str, step: int, extra: dict = None) -> dict:
        e = {
            "schema": "b4iu_snn_trace_event_v0.1",
            "seq": seq,
            "event_type": event_type,
            "t_ns": _T_BASE_NS + seq * 1_000_000,
            "step": step,
            "prev_hash": events[-1]["hash"] if events else GENESIS_HASH,
        }
        if extra:
            e.update(extra)
        e["hash"] = _event_hash(e)
        events.append(e)
        return e

    # Step 0: open / locality-check / close for unit_A (hop_count 1 ≤ H_max 2)
    _append(0, "STEP_START",     0, {"unit_id": "unit_A"})
    _append(1, "LOCALITY_CHECK", 0, {"unit_id": "unit_A", "hop_count": 1, "exception_reason": None})
    _append(2, "STEP_END",       0, {"unit_id": "unit_A"})

    trace_root = events[-1]["hash"]

    # ----------------------------------------------------------------- policy
    policy = {
        "schema": "b4iu_snn_policy_v0.1",
        "policy_version": POLICY_VERSION,
        "H_max": 2,
        "locality_event_types": ["LOCALITY_CHECK"],
        "hop_exceptions": [],
    }
    _write_json(os.path.join(run_dir, "policy.json"), policy)

    # ---------------------------------------------------------------- ida_root
    # Collect unique units sorted by unit_id.
    units = {}
    for e in events:
        uid = e.get("unit_id")
        if uid and uid not in units:
            units[uid] = {"unit_id": uid}
    unique_units = sorted(units.values(), key=lambda u: u["unit_id"])
    ida_root = _sha256(_c14n(unique_units))

    # ----------------------------------------------------------------- receipt
    receipt_body = {
        "schema": "b4iu_snn_receipt_v0.1",
        "run_id": run_id,
        "trace_root": trace_root,
        "ida_root": ida_root,
    }
    receipt = dict(receipt_body)
    receipt["sha256_c14n"] = _sha256(_c14n(receipt_body))
    _write_json(os.path.join(run_dir, "receipt.json"), receipt)

    # ----------------------------------------------------------------- verdict
    verdict = {
        "schema": "b4iu_snn_verdict_v0.1",
        "run_id": run_id,
        "verdict": "PASS",
        "policy_version": POLICY_VERSION,
        "reasons": [],
    }
    _write_json(os.path.join(run_dir, "verdict.json"), verdict)

    # ------------------------------------------------------------------ trace
    trace_path = os.path.join(run_dir, "trace.jsonl")
    with open(trace_path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, sort_keys=True, separators=(",", ":")) + "\n")

    # --------------------------------------------------------------- manifest
    artifacts = sorted(["manifest.json", "policy.json", "receipt.json", "trace.jsonl", "verdict.json"])
    manifest = {
        "schema": "b4iu_snn_manifest_v0.1",
        "run_id": run_id,
        "artifacts": artifacts,
    }
    _write_json(os.path.join(run_dir, "manifest.json"), manifest)

    print(f"Emitted synthetic run to: {run_dir}")


def _write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, sort_keys=True, indent=2)
        f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python -m tools.b4iu_snn_emit_synthetic_run <run_dir>", file=sys.stderr)
        sys.exit(1)
    emit(sys.argv[1])
