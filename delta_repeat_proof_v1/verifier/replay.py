"""Deterministic task replay.

Given a cognitive_task record the replay engine re-executes the declared
operation and compares the result against *expected_output*.  Any mismatch
is a hard failure — there is no tolerance or partial-credit path.

Supported operations
--------------------
sum   — sum of all integers in *inputs*
"""
from __future__ import annotations

from typing import Any, Dict


_OPERATORS: Dict[str, Any] = {
    "sum": sum,
}


class ReplayError(Exception):
    """Raised when the task cannot be replayed or the result does not match."""


def replay(task: Dict[str, Any]) -> int:
    """Re-execute *task* and return the computed result.

    Raises
    ------
    ReplayError
        If the operation is unknown, inputs are invalid, or the computed
        result does not equal *expected_output*.
    """
    operation = task.get("operation")
    inputs = task.get("inputs")
    expected = task.get("expected_output")

    if operation not in _OPERATORS:
        raise ReplayError(f"unknown operation: {operation!r}")

    if not isinstance(inputs, list):
        raise ReplayError("inputs must be a list")

    try:
        result = _OPERATORS[operation](inputs)
    except Exception as exc:
        raise ReplayError(f"execution failed: {exc}") from exc

    if result != expected:
        raise ReplayError(
            f"replay mismatch: computed {result!r}, expected {expected!r}"
        )

    return result
