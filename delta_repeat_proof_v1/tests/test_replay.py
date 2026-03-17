"""Tests for deterministic replay (verifier.replay)."""
import json
import pathlib

import pytest

from verifier.replay import verify_replay

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


def test_replay_passes_with_valid_artifacts():
    events = _load_events()
    ok, msg = verify_replay(events, BASE)
    assert ok is True, f"replay failed: {msg}"


def test_replay_detects_task_id_mismatch(tmp_path):
    events = _load_events()
    # Write a cognitive_task.json with wrong task_id.
    (tmp_path / "input").mkdir()
    task = {"expected_output": 6, "inputs": [1, 2, 3], "operation": "sum", "task_id": "task-9999"}
    (tmp_path / "input" / "cognitive_task.json").write_text(
        json.dumps(task), encoding="utf-8"
    )
    ok, msg = verify_replay(events, tmp_path)
    assert ok is False
    assert "task_id" in msg


def test_replay_detects_inputs_mismatch(tmp_path):
    events = _load_events()
    (tmp_path / "input").mkdir()
    task = {"expected_output": 10, "inputs": [4, 5, 1], "operation": "sum", "task_id": "task-0001"}
    (tmp_path / "input" / "cognitive_task.json").write_text(
        json.dumps(task), encoding="utf-8"
    )
    ok, msg = verify_replay(events, tmp_path)
    assert ok is False
    assert "inputs" in msg


def test_replay_detects_wrong_expected_output(tmp_path):
    events = _load_events()
    (tmp_path / "input").mkdir()
    # inputs correct but expected_output wrong
    task = {"expected_output": 99, "inputs": [1, 2, 3], "operation": "sum", "task_id": "task-0001"}
    (tmp_path / "input" / "cognitive_task.json").write_text(
        json.dumps(task), encoding="utf-8"
    )
    ok, msg = verify_replay(events, tmp_path)
    assert ok is False


def test_replay_detects_missing_file(tmp_path):
    events = _load_events()
    # No input/ directory at all.
    ok, msg = verify_replay(events, tmp_path)
    assert ok is False
    assert "cognitive_task.json" in msg
