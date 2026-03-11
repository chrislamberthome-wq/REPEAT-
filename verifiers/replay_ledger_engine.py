#!/usr/bin/env python3
"""
REPEAT Council Ledger Replay Engine (replay_ledger_engine.py).

Deterministically replays the council governance ledger from genesis,
recomputing state hashes at each step and verifying receipt chain integrity.

Exit codes:
  0 = all receipts replayed successfully; final state emitted to stdout as JSON
  1 = replay FAIL — hash chain broken, state mismatch, or invalid receipt
  2 = ERROR — infrastructure fault (file not found, JSON parse error, etc.)

This engine is part of the authoritative lane. Its outputs are the sole
authority for ledger state validity. Advisory tools (e.g. OpenCode) must
not reinterpret or override this engine's output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

SHA256_PREFIX = "sha256:"
COUNCIL_ID = "council_of_9"
SEAT_RANGE = range(1, 10)  # seats 1..9

GENESIS_STATE: Dict[str, Any] = {
    "schema_version": "c9-state-v1.0",
    "council_id": COUNCIL_ID,
    "ledger_seq": 0,
    "seats": {str(i): None for i in SEAT_RANGE},
    "quorum_threshold": 5,
}


def canonical_json(obj: Dict[str, Any]) -> bytes:
    """Canonical JSON per REPEAT C14N v1 (JCS / RFC 8785)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False,
    ).encode('utf-8')


def sha256_c14n(obj: Dict[str, Any]) -> str:
    """Compute SHA-256 of canonical JSON, prefixed with 'sha256:'."""
    digest = hashlib.sha256(canonical_json(obj)).hexdigest()
    return SHA256_PREFIX + digest


def compute_state_hash(state: Dict[str, Any]) -> str:
    """Compute state hash over all fields except state_hash_sha256."""
    state_for_hash = {k: v for k, v in state.items() if k != "state_hash_sha256"}
    return sha256_c14n(state_for_hash)


def apply_seat_fill(
    state: Dict[str, Any],
    receipt: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Apply a seat_fill action to the council state.

    Returns (new_state, errors). On success errors is empty.
    Fails if the seat is already occupied.
    """
    errors: List[str] = []
    seat_id = str(receipt.get("target_seat_id", ""))

    if seat_id not in state["seats"]:
        errors.append(f"seat_id '{seat_id}' not in valid seats 1..9")
        return None, errors

    if state["seats"][seat_id] is not None:
        errors.append(
            f"seat {seat_id} already occupied — duplicate seat fill"
        )
        return None, errors

    # Build new state (immutable copy)
    new_seats = {k: v for k, v in state["seats"].items()}
    new_seats[seat_id] = {
        "public_key": receipt.get(
            "candidate_public_key", receipt.get("entry_sha256", "unknown")
        ),
        "identity_hash_sha256": receipt.get(
            "candidate_identity_hash_sha256",
            receipt.get("entry_sha256", SHA256_PREFIX + "0" * 64),
        ),
        "filled_at_ledger_seq": receipt["ledger_seq"],
    }

    new_state: Dict[str, Any] = {
        "schema_version": "c9-state-v1.0",
        "council_id": COUNCIL_ID,
        "ledger_seq": receipt["ledger_seq"],
        "seats": new_seats,
        "quorum_threshold": state.get("quorum_threshold", 5),
    }
    return new_state, []


def replay_ledger(
    receipts: List[Dict[str, Any]],
) -> Tuple[str, str, Dict[str, Any], List[str]]:
    """
    Replay all receipts from genesis state.

    Returns (result, reason, final_state, errors).
    result is 'PASS', 'FAIL', or 'ERROR'.
    """
    errors: List[str] = []
    state = {k: v for k, v in GENESIS_STATE.items()}

    for i, receipt in enumerate(receipts):
        label = f"receipt[{i}] ledger_seq={receipt.get('ledger_seq', '?')}"

        # Required fields check
        required = [
            "receipt_type", "spec_version", "ledger_seq",
            "action", "target_seat_id", "council_id",
            "entry_sha256", "prev_state_sha256", "next_state_sha256",
            "result", "reason", "verified_at_utc",
        ]
        missing = [f for f in required if f not in receipt]
        if missing:
            errors.append(f"{label}: missing fields {missing}")
            return "FAIL", "missing_required_fields", state, errors

        # Sequence check
        expected_seq = state["ledger_seq"] + 1
        actual_seq = receipt["ledger_seq"]
        if actual_seq != expected_seq:
            errors.append(
                f"{label}: ledger_seq out of order: expected {expected_seq}, "
                f"got {actual_seq}"
            )
            return "FAIL", "sequence_error", state, errors

        # prev_state_sha256 must match current state hash
        current_state_hash = compute_state_hash(state)
        stored_prev = receipt["prev_state_sha256"]
        if stored_prev != current_state_hash:
            errors.append(
                f"{label}: prev_state_sha256 mismatch: "
                f"stored={stored_prev}, computed={current_state_hash}"
            )
            return "FAIL", "prev_state_hash_mismatch", state, errors

        # Only apply state transitions for PASS receipts
        receipt_result = receipt.get("result")
        if receipt_result == "PASS":
            action_type = receipt.get("action")
            if action_type == "seat_fill":
                new_state, apply_errors = apply_seat_fill(state, receipt)
                if apply_errors:
                    errors.extend(
                        f"{label}: {e}" for e in apply_errors
                    )
                    return "FAIL", "seat_fill_error", state, errors
                assert new_state is not None
                state = new_state
            else:
                errors.append(
                    f"{label}: unsupported action_type '{action_type}'"
                )
                return "FAIL", "unsupported_action", state, errors

            # Validate next_state_sha256 matches the state we produced
            computed_next = compute_state_hash(state)
            stored_next = receipt["next_state_sha256"]
            if stored_next != computed_next:
                errors.append(
                    f"{label}: next_state_sha256 mismatch: "
                    f"stored={stored_next}, computed={computed_next}"
                )
                return "FAIL", "next_state_hash_mismatch", state, errors

        elif receipt_result in ("FAIL", "ERROR"):
            # Non-PASS receipts do not mutate seat state; only advance ledger_seq
            state = {**state, "ledger_seq": actual_seq}
        else:
            errors.append(
                f"{label}: invalid result '{receipt_result}', "
                "must be PASS, FAIL, or ERROR"
            )
            return "FAIL", "invalid_result_field", state, errors

    return "PASS", "replay_ok", state, []


def load_receipts(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Load JSONL receipts. Returns (receipts, parse_errors)."""
    receipts: List[Dict[str, Any]] = []
    parse_errors: List[str] = []
    try:
        with open(path, 'r') as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    receipts.append(json.loads(line))
                except json.JSONDecodeError as e:
                    parse_errors.append(f"line {lineno}: JSON parse error: {e}")
    except OSError as e:
        raise RuntimeError(f"Cannot open '{path}': {e}") from e
    return receipts, parse_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "REPEAT council ledger replay engine — "
            "deterministic state reconstruction from JSONL receipts."
        )
    )
    parser.add_argument(
        "ledger",
        nargs="?",
        default="receipts/council_ledger.jsonl",
        help="Path to JSONL ledger file (default: receipts/council_ledger.jsonl).",
    )
    args = parser.parse_args()

    try:
        receipts, parse_errors = load_receipts(args.ledger)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if parse_errors:
        for err in parse_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 2

    result, reason, final_state, errors = replay_ledger(receipts)

    if result == "PASS":
        state_with_hash = {
            **final_state,
            "state_hash_sha256": compute_state_hash(final_state),
        }
        print(
            json.dumps(state_with_hash, ensure_ascii=False, sort_keys=True, indent=2)
        )
        print(f"\nPASS: {reason} ({len(receipts)} receipt(s) replayed)", file=sys.stderr)
        return 0

    for err in errors:
        print(f"{result}: {err}", file=sys.stderr)
    print(f"\n{result}: {reason}", file=sys.stderr)
    return 1 if result == "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())
