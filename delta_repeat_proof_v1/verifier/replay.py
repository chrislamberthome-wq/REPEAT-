"""Deterministic replay verifier.

Re-executes the cognitive task from ``input/cognitive_task.json`` and
confirms the result matches the payload recorded in the ``reflect`` stage.
"""
import json
import pathlib
from typing import Any, Dict, List, Tuple

_OPERATIONS: Dict[str, Any] = {
    "sum": lambda inputs: sum(inputs),
}


def verify_replay(
    events: List[Dict[str, Any]],
    base: pathlib.Path,
) -> Tuple[bool, str]:
    """Return ``(True, 'ok')`` when replay succeeds, ``(False, reason)`` otherwise."""
    task_path = base / "input" / "cognitive_task.json"
    try:
        with open(task_path, encoding="utf-8") as fh:
            task = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return False, f"cannot load cognitive_task.json: {exc}"

    reflect = next((e for e in events if e.get("stage") == "reflect"), None)
    if reflect is None:
        return False, "no reflect stage in trace"

    rp = reflect["payload"]
    if rp.get("task_id") != task.get("task_id"):
        return False, (
            f"task_id mismatch: trace={rp.get('task_id')!r} "
            f"file={task.get('task_id')!r}"
        )
    if rp.get("operation") != task.get("operation"):
        return False, "operation mismatch between trace and cognitive_task.json"
    if rp.get("inputs") != task.get("inputs"):
        return False, "inputs mismatch between trace and cognitive_task.json"

    op_name = task.get("operation")
    if op_name not in _OPERATIONS:
        return False, f"unknown operation: {op_name!r}"

    result = _OPERATIONS[op_name](task["inputs"])
    expected = task.get("expected_output")
    if result != expected:
        return False, f"replay result {result!r} != expected {expected!r}"

    return True, "ok"
