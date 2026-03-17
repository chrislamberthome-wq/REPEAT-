"""Tests for deterministic task replay.

Guarantees under test
---------------------
- sum([1, 2, 3]) == 6 (golden task passes).
- Wrong expected_output raises ReplayError (mismatch is FAIL).
- Unknown operation raises ReplayError.
- Non-list inputs raises ReplayError.
- replay() result equals expected_output exactly.
"""
import json
from pathlib import Path

import pytest

from delta_repeat_proof_v1.verifier.replay import ReplayError, replay

_ROOT = Path(__file__).resolve().parent.parent
_TASK_PATH = _ROOT / "input" / "cognitive_task.json"


def _load_task():
    return json.loads(_TASK_PATH.read_bytes())


def test_golden_task_passes():
    task = _load_task()
    result = replay(task)
    assert result == 6


def test_replay_is_deterministic():
    task = _load_task()
    r1 = replay(task)
    r2 = replay(task)
    assert r1 == r2


def test_wrong_expected_output_fails():
    task = dict(_load_task())
    task["expected_output"] = 99
    with pytest.raises(ReplayError, match="mismatch"):
        replay(task)


def test_unknown_operation_fails():
    task = dict(_load_task())
    task["operation"] = "multiply"
    with pytest.raises(ReplayError, match="unknown operation"):
        replay(task)


def test_non_list_inputs_fails():
    task = dict(_load_task())
    task["inputs"] = "1,2,3"
    with pytest.raises(ReplayError, match="inputs must be a list"):
        replay(task)


def test_empty_inputs():
    task = {
        "task_id": "task-0002",
        "operation": "sum",
        "inputs": [],
        "expected_output": 0,
    }
    result = replay(task)
    assert result == 0


def test_single_element_sum():
    task = {
        "task_id": "task-0003",
        "operation": "sum",
        "inputs": [42],
        "expected_output": 42,
    }
    result = replay(task)
    assert result == 42


def test_task_file_has_correct_fields():
    task = _load_task()
    assert task["task_id"] == "task-0001"
    assert task["operation"] == "sum"
    assert task["inputs"] == [1, 2, 3]
    assert task["expected_output"] == 6
