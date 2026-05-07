#!/usr/bin/env python3
"""
delta_repeat_proof_v1 verifier.

Run from within delta_repeat_proof_v1/:
    python verifier/verify.py

Exit codes:
    0 = PASS  (all checks passed, receipt written to receipt/receipt.json)
    1 = FAIL  (validation failure: hash chain, canonicalization, replay, or governance)
    2 = ERROR (runtime error: missing files, JSON parse errors)

Validates:
    1. Each trace step is stored in canonical JSON form (sorted keys, compact)
    2. Each step's hash matches sha256(canonical(step_without_hash))
    3. Each step's prev_hash chains correctly to the previous step
    4. No governance step issues a DENY verdict
    5. Task execution output matches expected_output in input/cognitive_task.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

TRACE_PATH = "trace.jsonl"
INPUT_PATH = "input/cognitive_task.json"
RECEIPT_PATH = "receipt/receipt.json"
GENESIS_HASH = "0" * 64


def canonical_json(obj: Any) -> bytes:
    """Canonical JSON: sorted keys, no extra whitespace, UTF-8 encoded."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_step_hash(step: Dict[str, Any]) -> str:
    """Compute the hash of a step, excluding the 'hash' field."""
    step_without_hash = {k: v for k, v in step.items() if k != "hash"}
    return sha256hex(canonical_json(step_without_hash))


def write_receipt(status: str, details: Dict[str, Any]) -> None:
    """Write a deterministic receipt to RECEIPT_PATH."""
    receipt: Dict[str, Any] = {"artifact": "delta_repeat_proof_v1", "status": status}
    receipt.update(details)
    # receipt_sha256 is computed over the receipt without itself
    receipt["receipt_sha256"] = sha256hex(canonical_json(receipt))
    os.makedirs(os.path.dirname(RECEIPT_PATH), exist_ok=True)
    with open(RECEIPT_PATH, "w") as f:
        f.write(canonical_json(receipt).decode("utf-8"))
        f.write("\n")


def load_task(path: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with open(path, "r") as f:
            return json.load(f), None
    except OSError as e:
        return None, f"Cannot open {path}: {e}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"


def load_trace(
    path: str,
) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Load trace steps from a JSONL file.

    Returns (steps, parse_errors, canon_errors).
    parse_errors are fatal (exit 2).
    canon_errors are validation failures (exit 1).
    """
    steps: List[Dict[str, Any]] = []
    parse_errors: List[str] = []
    canon_errors: List[str] = []
    try:
        with open(path, "r") as f:
            raw_lines = [line for line in f if line.strip()]
    except OSError as e:
        parse_errors.append(f"Cannot open {path}: {e}")
        return steps, parse_errors, canon_errors

    for lineno, raw_line in enumerate(raw_lines, 1):
        stripped = raw_line.rstrip("\n")
        try:
            step = json.loads(stripped)
        except json.JSONDecodeError as e:
            parse_errors.append(f"trace.jsonl line {lineno}: JSON parse error: {e}")
            continue
        if not isinstance(step, dict):
            parse_errors.append(f"trace.jsonl line {lineno}: expected JSON object")
            continue
        # Canonicalization check: raw line must equal canonical form
        expected_raw = canonical_json(step).decode("utf-8")
        if stripped != expected_raw:
            canon_errors.append(
                f"trace.jsonl line {lineno}: not in canonical form "
                f"(add whitespace or key reorder detected)"
            )
        steps.append(step)

    return steps, parse_errors, canon_errors


def validate_chain(
    steps: List[Dict[str, Any]],
) -> Tuple[List[str], Optional[str], str]:
    """
    Validate hash chain, governance, and collect execution output.

    Returns (errors, replay_output, governance_verdict).
    """
    errors: List[str] = []
    prev_hash = GENESIS_HASH
    replay_output: Optional[str] = None
    governance_verdict = "ALLOW"

    for i, step in enumerate(steps):
        step_num = i + 1

        if "hash" not in step:
            errors.append(f"step {step_num}: missing 'hash' field")
            prev_hash = step.get("hash", prev_hash)
            continue

        stored_prev = step.get("prev_hash", "")
        if stored_prev != prev_hash:
            errors.append(
                f"step {step_num}: prev_hash mismatch — "
                f"expected {prev_hash[:16]}…, got {str(stored_prev)[:16]}…"
            )

        expected_hash = compute_step_hash(step)
        if step["hash"] != expected_hash:
            errors.append(
                f"step {step_num}: hash mismatch — "
                f"stored {step['hash'][:16]}…, computed {expected_hash[:16]}…"
            )

        if step.get("action") == "governance_check":
            verdict = step.get("verdict", "UNKNOWN")
            if verdict == "DENY":
                governance_verdict = "DENY"
                errors.append(
                    f"step {step_num}: governance DENY — execution halted"
                )

        if step.get("action") == "task_execution":
            replay_output = step.get("output")

        prev_hash = step.get("hash", prev_hash)

    return errors, replay_output, governance_verdict


def main() -> int:
    task, task_err = load_task(INPUT_PATH)
    if task_err is not None:
        print(f"ERROR: {task_err}", file=sys.stderr)
        return 2

    expected_output = task.get("expected_output")

    steps, parse_errors, canon_errors = load_trace(TRACE_PATH)

    if parse_errors:
        for err in parse_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    if not steps:
        print("ERROR: trace.jsonl contains no steps", file=sys.stderr)
        return 2

    all_errors: List[str] = list(canon_errors)

    chain_errors, replay_output, governance_verdict = validate_chain(steps)
    all_errors.extend(chain_errors)

    replay_match = replay_output == expected_output
    if not replay_match:
        all_errors.append(
            f"replay mismatch — expected={expected_output!r}, got={replay_output!r}"
        )

    status = "FAIL" if all_errors else "PASS"
    trace_hash = sha256hex(canonical_json(steps))

    details: Dict[str, Any] = {
        "governance_verdict": governance_verdict,
        "replay_match": replay_match,
        "steps": len(steps),
        "trace_hash": trace_hash,
    }
    if all_errors:
        details["errors"] = all_errors

    for err in all_errors:
        print(f"FAIL: {err}", file=sys.stderr)

    try:
        write_receipt(status, details)
    except OSError as e:
        print(f"ERROR: Cannot write receipt: {e}", file=sys.stderr)
        return 2

    if status == "PASS":
        print(
            f"PASS: {len(steps)} step(s) verified. "
            f"Receipt written to {RECEIPT_PATH}"
        )
        return 0
    else:
        print(
            f"FAIL: {len(all_errors)} error(s). "
            f"Receipt written to {RECEIPT_PATH}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
