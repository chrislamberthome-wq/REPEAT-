#!/usr/bin/env python3
"""Independent verifier for delta_repeat_proof_v1.

Exit codes
----------
0  PASS – all conditions hold.
1  FAIL – an explicit violation was detected (tamper, wrong verdict, …).
2  ERROR – input is unreadable, malformed, or tooling fault.

Usage::

    python verifier/verify.py [--base-dir PATH]
"""
import argparse
import json
import pathlib
import sys

from verifier.canonical import canonical_bytes, canonical_hash

_GENESIS_PREV = "sha256:" + "0" * 64
_STAGES = ("reflect", "plan", "learn", "regulate", "govern")


def _load_trace(base: pathlib.Path):
    trace_path = base / "trace" / "trace.jsonl"
    events = []
    try:
        with open(trace_path, encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                stripped = raw.rstrip("\n")
                if not stripped:
                    continue
                # Reject non-canonical JSON (extra whitespace, wrong key order).
                try:
                    obj = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    _die_error(f"trace line {lineno}: JSON parse error: {exc}")
                canonical = canonical_bytes(obj).decode("utf-8")
                if stripped != canonical:
                    _die_fail(
                        f"trace line {lineno}: non-canonical JSON "
                        f"(expected {canonical!r}, got {stripped!r})"
                    )
                events.append(obj)
    except OSError as exc:
        _die_error(f"cannot open trace: {exc}")
    if not events:
        _die_error("trace is empty")
    return events


def _verify_hash_chain(events):
    for i, event in enumerate(events):
        expected_prev = _GENESIS_PREV if i == 0 else canonical_hash(
            {k: v for k, v in events[i - 1].items() if k != "event_hash"}
        )
        if event.get("prev_hash") != expected_prev:
            _die_fail(
                f"event seq={event.get('seq')}: prev_hash mismatch "
                f"(expected {expected_prev!r})"
            )
        body = {k: v for k, v in event.items() if k != "event_hash"}
        expected_hash = canonical_hash(body)
        if event.get("event_hash") != expected_hash:
            _die_fail(
                f"event seq={event.get('seq')}: event_hash mismatch "
                f"(expected {expected_hash!r})"
            )


def _verify_stages(events):
    stages = [e.get("stage") for e in events]
    if len(stages) != 5:
        _die_fail(f"expected 5 stages, got {len(stages)}")
    if stages != list(_STAGES):
        _die_fail(f"stages out of order: {stages}")


def _verify_governance(events):
    govern = next((e for e in events if e.get("stage") == "govern"), None)
    if govern is None:
        _die_fail("no govern stage in trace")
    verdict = govern["payload"].get("verdict")
    if verdict != "ALLOW":
        _die_fail(f"governance verdict is {verdict!r}; execution halted")


def _die_fail(msg: str) -> None:
    print(f"FAIL: {msg}", flush=True)
    sys.exit(1)


def _die_error(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(2)


def _get_base(args) -> pathlib.Path:
    if args.base_dir:
        return pathlib.Path(args.base_dir).resolve()
    return pathlib.Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-dir",
        metavar="PATH",
        help="Root of delta_repeat_proof_v1 (default: parent of verifier/)",
    )
    args = parser.parse_args()
    base = _get_base(args)

    # 1. Load & canonicality check
    events = _load_trace(base)

    # 2. Stage order
    _verify_stages(events)

    # 3. Hash chain
    _verify_hash_chain(events)

    # 4. Governance (DENY halts)
    _verify_governance(events)

    # 5. Replay
    from verifier.replay import verify_replay  # noqa: PLC0415

    ok, msg = verify_replay(events, base)
    if not ok:
        _die_fail(f"replay: {msg}")

    # 6. Receipt
    from verifier.receipt import verify_receipt  # noqa: PLC0415

    ok, msg = verify_receipt(events, base)
    if not ok:
        _die_fail(f"receipt: {msg}")

    print("PASS", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
