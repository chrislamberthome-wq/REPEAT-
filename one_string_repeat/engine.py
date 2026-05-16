"""
engine.py — Rule engine for one_string_REPEAT v1.0.

Executes payloads and returns deterministic output dicts.

Supported rules:
    fixed_point  — iterates f(x) = x until the value stabilises or max_steps
                   is exhausted.  Since f is the identity, any initial_value
                   is a fixed point after exactly 1 step.

Exit-code convention:
    0  PASS   — execution completed successfully
    1  FAIL   — rule ran but did not converge within max_steps
    2  ERROR  — invalid input or unhandled exception

Fail-closed: any unrecognised rule or malformed input returns ERROR immediately.
"""
from __future__ import annotations

from typing import Any

RESULT_PASS = "PASS"
RESULT_FAIL = "FAIL"
RESULT_ERROR = "ERROR"

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2

_KNOWN_RULES = frozenset({"fixed_point"})


def _run_fixed_point(
    initial_value: int,
    max_steps: int,
) -> tuple[str, int, dict[str, Any], list[str]]:
    """
    Execute the fixed_point rule.

    f(x) = x (identity).  The value is stable from the first step, so:
        final_value      = initial_value
        steps_executed   = 1
        fixed_point_reached = True

    Returns (result, exit_code, output_dict, errors).
    """
    if not isinstance(initial_value, int) or isinstance(initial_value, bool):
        return RESULT_ERROR, EXIT_ERROR, {}, [
            f"initial_value must be an integer, got {type(initial_value).__name__}"
        ]
    if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
        return RESULT_ERROR, EXIT_ERROR, {}, [
            f"max_steps must be a positive integer, got {max_steps!r}"
        ]

    value = initial_value
    steps = 0
    fixed = False

    for _ in range(max_steps):
        next_value = value  # f(x) = x
        steps += 1
        if next_value == value:
            fixed = True
            value = next_value
            break
        value = next_value

    if fixed:
        output = {
            "final_value": value,
            "steps_executed": steps,
            "fixed_point_reached": True,
        }
        return RESULT_PASS, EXIT_PASS, output, []
    else:
        output = {
            "final_value": value,
            "steps_executed": steps,
            "fixed_point_reached": False,
        }
        return RESULT_FAIL, EXIT_FAIL, output, ["fixed point not reached within max_steps"]


def execute(payload_input: dict[str, Any]) -> tuple[str, int, dict[str, Any], list[str]]:
    """
    Execute the rule described in *payload_input*.

    *payload_input* is the ``"input"`` sub-object of a validated
    ``one_string_payload``.

    Returns ``(result, exit_code, output, errors)`` where:
        result     — "PASS" | "FAIL" | "ERROR"
        exit_code  — 0 | 1 | 2
        output     — deterministic output dict (empty dict on ERROR)
        errors     — list of error strings (empty on PASS)

    Fail-closed: any structural problem returns ERROR immediately.
    """
    if not isinstance(payload_input, dict):
        return RESULT_ERROR, EXIT_ERROR, {}, [
            f"payload input must be a dict, got {type(payload_input).__name__}"
        ]

    rule = payload_input.get("rule")
    if rule is None:
        return RESULT_ERROR, EXIT_ERROR, {}, ["missing required field: rule"]
    if rule not in _KNOWN_RULES:
        return RESULT_ERROR, EXIT_ERROR, {}, [f"unknown rule: {rule!r}"]

    try:
        if rule == "fixed_point":
            initial_value = payload_input.get("initial_value")
            max_steps = payload_input.get("max_steps")
            if initial_value is None:
                return RESULT_ERROR, EXIT_ERROR, {}, ["missing required field: initial_value"]
            if max_steps is None:
                return RESULT_ERROR, EXIT_ERROR, {}, ["missing required field: max_steps"]
            return _run_fixed_point(initial_value, max_steps)
    except Exception as exc:  # noqa: BLE001
        return RESULT_ERROR, EXIT_ERROR, {}, [f"engine exception: {exc}"]

    return RESULT_ERROR, EXIT_ERROR, {}, [f"unhandled rule: {rule!r}"]
