"""Top-level verifier for delta_repeat_proof_v1.

Validates all six guarantees in strict order:

1. Schema conformance  — every trace event and governance record matches
                         its JSON Schema; receipt matches receipt schema.
2. Canonicalization    — every trace line is already in canonical form.
3. Hash chain          — event_hash and prev_hash chain is unbroken.
4. Governance          — verdict is ALLOW; DENY halts immediately.
5. Replay              — deterministic task re-execution matches expected.
6. Receipt             — trace_sha256 and crc16_ccitt_false re-derive correctly.

Exit semantics (when used as __main__)
--------------------------------------
0 — all guarantees pass  → status PASS
1 — explicit violation   → status FAIL
2 — structural / tooling fault → status ERROR

Any FAIL or ERROR is fail-closed; the verifier never continues past a
detected violation.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

from .canonical import canonical_bytes, canonical_sha256, sha256_hex
from .receipt import ReceiptVerificationError, verify_receipt
from .replay import ReplayError, replay

# ---------------------------------------------------------------------------
# Paths (relative to this file's package root, i.e. delta_repeat_proof_v1/)
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_schema(name: str) -> Dict[str, Any]:
    return _load_json(_ROOT / "schemas" / name)


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
    return events


# ---------------------------------------------------------------------------
# Individual guarantee checks
# ---------------------------------------------------------------------------

EXPECTED_STAGES = ["reflect", "plan", "learn", "regulate", "govern"]


def check_schema_conformance(
    events: List[Dict[str, Any]],
    governance: Dict[str, Any],
    receipt: Dict[str, Any],
) -> None:
    """Validate all records against their JSON Schemas."""
    event_schema = _load_schema("event.schema.json")
    gov_schema = _load_schema("governance.schema.json")
    receipt_schema = _load_schema("receipt.schema.json")

    for i, event in enumerate(events):
        try:
            jsonschema.validate(event, event_schema)
        except jsonschema.ValidationError as exc:
            raise ValueError(f"event[{i}] schema violation: {exc.message}") from exc

    try:
        jsonschema.validate(governance, gov_schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"governance schema violation: {exc.message}") from exc

    try:
        jsonschema.validate(receipt, receipt_schema)
    except jsonschema.ValidationError as exc:
        raise ValueError(f"receipt schema violation: {exc.message}") from exc


def check_canonicalization(events: List[Dict[str, Any]], raw_lines: List[str]) -> None:
    """Each trace line must already be in canonical form."""
    for i, (event, raw_line) in enumerate(zip(events, raw_lines)):
        expected = canonical_bytes(event).decode("utf-8")
        if raw_line != expected:
            raise ValueError(
                f"event[{i}] is not in canonical form.\n"
                f"  stored : {raw_line!r}\n"
                f"  canonical: {expected!r}"
            )


def check_hash_chain(events: List[Dict[str, Any]]) -> None:
    """Verify event_hash values and the prev_hash chain."""
    if len(events) != len(EXPECTED_STAGES):
        raise ValueError(
            f"expected {len(EXPECTED_STAGES)} events, got {len(events)}"
        )

    for i, (event, expected_stage) in enumerate(zip(events, EXPECTED_STAGES)):
        if event["stage"] != expected_stage:
            raise ValueError(
                f"event[{i}]: expected stage {expected_stage!r}, "
                f"got {event['stage']!r}"
            )

        # Re-derive event_hash: hash of canonical JSON excluding event_hash field
        without_hash = {k: v for k, v in event.items() if k != "event_hash"}
        expected_hash = canonical_sha256(without_hash)
        if event["event_hash"] != expected_hash:
            raise ValueError(
                f"event[{i}] ({event['stage']}): event_hash mismatch: "
                f"stored={event['event_hash']!r}, computed={expected_hash!r}"
            )

        # Verify prev_hash linkage
        if i == 0:
            if event["prev_hash"] is not None:
                raise ValueError(
                    f"event[0] ({event['stage']}): prev_hash must be null for "
                    f"first event, got {event['prev_hash']!r}"
                )
        else:
            expected_prev = events[i - 1]["event_hash"]
            if event["prev_hash"] != expected_prev:
                raise ValueError(
                    f"event[{i}] ({event['stage']}): prev_hash chain broken: "
                    f"stored={event['prev_hash']!r}, "
                    f"expected={expected_prev!r}"
                )


def check_governance(governance: Dict[str, Any]) -> None:
    """DENY verdict halts immediately."""
    verdict = governance.get("verdict")
    if verdict == "DENY":
        raise ValueError(
            f"governance DENY: execution halted. "
            f"constraints_applied={governance.get('constraints_applied')}"
        )
    if verdict != "ALLOW":
        raise ValueError(f"governance verdict must be ALLOW or DENY, got {verdict!r}")


def check_replay(task: Dict[str, Any]) -> None:
    """Re-execute the deterministic task; mismatch is a hard failure."""
    try:
        replay(task)
    except ReplayError as exc:
        raise ValueError(str(exc)) from exc


def check_receipt(receipt: Dict[str, Any], trace_bytes: bytes) -> None:
    """Verify trace_sha256 and crc16_ccitt_false re-derive correctly."""
    try:
        verify_receipt(receipt, trace_bytes)
    except ReceiptVerificationError as exc:
        raise ValueError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_verification(root: Path = _ROOT) -> Dict[str, Any]:
    """Run all six checks and return a result dict.

    Returns
    -------
    dict with keys: status ("PASS" | "FAIL" | "ERROR"), message (str)
    """
    try:
        # Load inputs
        task = _load_json(root / "input" / "cognitive_task.json")

        trace_path = root / "trace" / "trace.jsonl"
        trace_raw_bytes = trace_path.read_bytes()
        raw_lines: List[str] = []
        with trace_path.open(encoding="utf-8") as fh:
            for line in fh:
                stripped = line.rstrip("\n")
                if stripped:
                    raw_lines.append(stripped)
        events = [json.loads(line) for line in raw_lines]

        # Load governance from last event payload or dedicated record
        # The governance record is embedded as a separate JSON file
        gov_path = root / "trace" / "governance.json"
        if gov_path.exists():
            governance = _load_json(gov_path)
        else:
            # derive from last event (govern stage)
            gov_event = next(
                (e for e in reversed(events) if e.get("stage") == "govern"), None
            )
            if gov_event is None:
                raise ValueError("no governance record found")
            # The governance record is stored inline in the govern stage payload
            # For this artifact it is a dedicated file under trace/
            raise ValueError("governance.json not found under trace/")

        receipt = _load_json(root / "receipt" / "receipt.json")

        # 1. Schema conformance
        check_schema_conformance(events, governance, receipt)

        # 2. Canonicalization
        check_canonicalization(events, raw_lines)

        # 3. Hash chain
        check_hash_chain(events)

        # 4. Governance
        check_governance(governance)

        # 5. Replay
        check_replay(task)

        # 6. Receipt
        check_receipt(receipt, trace_raw_bytes)

    except ValueError as exc:
        return {"status": "FAIL", "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"status": "ERROR", "message": f"{type(exc).__name__}: {exc}"}

    return {"status": "PASS", "message": "all guarantees satisfied"}


if __name__ == "__main__":
    result = run_verification()
    print(json.dumps(result, indent=2))
    if result["status"] == "PASS":
        sys.exit(0)
    elif result["status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(2)
