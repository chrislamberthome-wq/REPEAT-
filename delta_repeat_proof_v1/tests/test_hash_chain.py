"""Tests for the hash chain in trace/trace.jsonl."""
import json
import pathlib

import pytest

from verifier.canonical import canonical_hash

BASE = pathlib.Path(__file__).resolve().parent.parent
_GENESIS_PREV = "sha256:" + "0" * 64
_EXPECTED_STAGES = ["reflect", "plan", "learn", "regulate", "govern"]


def _load_events():
    trace_path = BASE / "trace" / "trace.jsonl"
    events = []
    with open(trace_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line:
                events.append(json.loads(line))
    return events


def test_trace_has_five_events():
    assert len(_load_events()) == 5


def test_stages_in_order():
    stages = [e["stage"] for e in _load_events()]
    assert stages == _EXPECTED_STAGES


def test_seq_values():
    seqs = [e["seq"] for e in _load_events()]
    assert seqs == [1, 2, 3, 4, 5]


def test_cycle_id_consistent():
    events = _load_events()
    cycle_ids = {e["cycle_id"] for e in events}
    assert cycle_ids == {"cycle-0001"}


def test_genesis_prev_hash():
    events = _load_events()
    assert events[0]["prev_hash"] == _GENESIS_PREV


def test_hash_chain_unbroken():
    events = _load_events()
    for i in range(1, len(events)):
        prev_body = {k: v for k, v in events[i - 1].items() if k != "event_hash"}
        expected = canonical_hash(prev_body)
        assert events[i]["prev_hash"] == expected, (
            f"event seq={events[i]['seq']}: prev_hash mismatch"
        )


def test_event_hashes_valid():
    events = _load_events()
    for event in events:
        body = {k: v for k, v in event.items() if k != "event_hash"}
        expected = canonical_hash(body)
        assert event["event_hash"] == expected, (
            f"event seq={event['seq']}: event_hash invalid"
        )


def test_each_line_is_canonical_json():
    trace_path = BASE / "trace" / "trace.jsonl"
    with open(trace_path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            stripped = raw.rstrip("\n")
            if not stripped:
                continue
            obj = json.loads(stripped)
            canonical = json.dumps(
                obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            assert stripped == canonical, (
                f"line {lineno} is not canonical JSON"
            )
