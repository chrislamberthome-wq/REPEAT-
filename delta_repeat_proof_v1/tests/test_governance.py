"""Tests for the governance record in the govern stage."""
import json
import pathlib

import pytest

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


def _govern_payload():
    events = _load_events()
    govern = next(e for e in events if e["stage"] == "govern")
    return govern["payload"]


def test_govern_stage_present():
    events = _load_events()
    stages = [e["stage"] for e in events]
    assert "govern" in stages


def test_govern_is_last_stage():
    events = _load_events()
    assert events[-1]["stage"] == "govern"


def test_verdict_is_allow():
    assert _govern_payload()["verdict"] == "ALLOW"


def test_decision_id_format():
    payload = _govern_payload()
    assert payload["decision_id"].startswith("gov-")


def test_cycle_id_matches():
    payload = _govern_payload()
    assert payload["cycle_id"] == "cycle-0001"


def test_constraints_applied_present():
    payload = _govern_payload()
    constraints = payload["constraints_applied"]
    assert isinstance(constraints, list)
    assert len(constraints) >= 1


def test_constraints_applied_values():
    payload = _govern_payload()
    assert "max_nodes<=3" in payload["constraints_applied"]
    assert "posture!=LOCKDOWN" in payload["constraints_applied"]
