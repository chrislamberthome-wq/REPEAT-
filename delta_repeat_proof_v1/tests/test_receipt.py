"""Tests for the execution receipt (verifier.receipt)."""
import hashlib
import json
import pathlib

import pytest

from verifier.receipt import verify_receipt

BASE = pathlib.Path(__file__).resolve().parent.parent


def _load_events():
    trace_path = BASE / "trace" / "trace.jsonl"
    events = []
    with open(trace_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line:
                events.append(json.loads(line))
    return events


def test_receipt_passes_with_valid_artifacts():
    events = _load_events()
    ok, msg = verify_receipt(events, BASE)
    assert ok is True, f"receipt verification failed: {msg}"


def test_receipt_status_is_pass():
    receipt_path = BASE / "receipt" / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "PASS"


def test_receipt_trace_sha256_matches_file():
    receipt_path = BASE / "receipt" / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    trace_bytes = (BASE / "trace" / "trace.jsonl").read_bytes()
    expected = "sha256:" + hashlib.sha256(trace_bytes).hexdigest()
    assert receipt["trace_sha256"] == expected


def test_receipt_detects_wrong_trace_hash(tmp_path):
    """If trace.jsonl is tampered, trace_sha256 in receipt should mismatch."""
    import shutil

    # Copy artifacts to tmp_path.
    for d in ("trace", "receipt", "input"):
        shutil.copytree(BASE / d, tmp_path / d)

    # Tamper: append a space to trace.jsonl.
    trace_path = tmp_path / "trace" / "trace.jsonl"
    trace_path.write_bytes(trace_path.read_bytes() + b" ")

    events = _load_events()
    ok, msg = verify_receipt(events, tmp_path)
    assert ok is False
    assert "trace_sha256" in msg


def test_receipt_detects_fail_status(tmp_path):
    import shutil

    for d in ("trace", "receipt", "input"):
        shutil.copytree(BASE / d, tmp_path / d)

    receipt_path = tmp_path / "receipt" / "receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["status"] = "FAIL"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    events = _load_events()
    ok, msg = verify_receipt(events, tmp_path)
    assert ok is False
    assert "status" in msg
