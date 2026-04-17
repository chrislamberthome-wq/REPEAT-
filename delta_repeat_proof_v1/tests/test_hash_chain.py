"""Tests for the trace hash chain integrity.

Guarantees under test
---------------------
- The stored trace.jsonl has the correct trace_sha256 as referenced in receipt.
- Each event's event_hash is derived from its canonical JSON (minus event_hash).
- Each event's prev_hash points to the previous event's event_hash.
- The first event's prev_hash is null.
- Mutating any field in any event breaks the chain (FAIL, not silent pass).
- Wrong number of events is rejected.
- Out-of-order stages are rejected.
"""
import copy
import json
from pathlib import Path

import pytest

from delta_repeat_proof_v1.verifier.canonical import canonical_sha256, sha256_hex
from delta_repeat_proof_v1.verifier.verify import check_hash_chain, check_canonicalization

_ROOT = Path(__file__).resolve().parent.parent
_TRACE = _ROOT / "trace" / "trace.jsonl"


def _load_events():
    events = []
    raw_lines = []
    with _TRACE.open(encoding="utf-8") as fh:
        for line in fh:
            stripped = line.rstrip("\n")
            if stripped:
                raw_lines.append(stripped)
                events.append(json.loads(stripped))
    return events, raw_lines


def test_trace_has_five_events():
    events, _ = _load_events()
    assert len(events) == 5


def test_stages_are_in_order():
    events, _ = _load_events()
    expected = ["reflect", "plan", "learn", "regulate", "govern"]
    actual = [e["stage"] for e in events]
    assert actual == expected


def test_first_event_prev_hash_is_null():
    events, _ = _load_events()
    assert events[0]["prev_hash"] is None


def test_hash_chain_passes():
    events, _ = _load_events()
    check_hash_chain(events)  # must not raise


def test_canonicalization_passes():
    events, raw_lines = _load_events()
    check_canonicalization(events, raw_lines)  # must not raise


def test_each_event_hash_is_correct():
    events, _ = _load_events()
    for i, event in enumerate(events):
        without_hash = {k: v for k, v in event.items() if k != "event_hash"}
        expected = canonical_sha256(without_hash)
        assert event["event_hash"] == expected, (
            f"event[{i}] ({event['stage']}): hash mismatch"
        )


def test_each_prev_hash_links_correctly():
    events, _ = _load_events()
    for i in range(1, len(events)):
        assert events[i]["prev_hash"] == events[i - 1]["event_hash"], (
            f"event[{i}] prev_hash does not link to event[{i-1}] event_hash"
        )


def test_trace_sha256_matches_receipt():
    trace_bytes = _TRACE.read_bytes()
    actual_sha = sha256_hex(trace_bytes)
    receipt_path = _ROOT / "receipt" / "receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    assert receipt["trace_sha256"] == actual_sha


def test_mutated_payload_breaks_chain():
    events, _ = _load_events()
    mutated = copy.deepcopy(events)
    mutated[0]["payload"]["note"] = "tampered"
    with pytest.raises(ValueError, match="event_hash mismatch"):
        check_hash_chain(mutated)


def test_mutated_stage_breaks_chain():
    events, _ = _load_events()
    mutated = copy.deepcopy(events)
    mutated[2]["stage"] = "plan"  # duplicate stage, wrong order
    with pytest.raises(ValueError):
        check_hash_chain(mutated)


def test_wrong_event_count_rejected():
    events, _ = _load_events()
    with pytest.raises(ValueError, match="expected 5 events"):
        check_hash_chain(events[:3])


def test_non_canonical_trace_line_fails():
    events, _ = _load_events()
    # Serialize with non-canonical whitespace
    non_canonical_lines = [
        json.dumps(e, sort_keys=True, indent=2)
        for e in events
    ]
    with pytest.raises(ValueError, match="canonical"):
        check_canonicalization(events, non_canonical_lines)
