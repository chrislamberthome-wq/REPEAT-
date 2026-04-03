"""Authoritative verifier for blood-ion-repeat experiment traces.

Usage::

    python -m blood_ion_repeat.verifier <trace.jsonl> [--receipt <out.json>]

The verifier is the ground-truth pass/fail authority.  ``run_experiment.py``
emits provisional receipts; this module produces the canonical receipt that
should be used for any audit or publication purpose.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from .crc16 import crc16_hex
from .receipt import build_receipt
from .trace import load_trace


def verify_trace(
    trace_path: Path | str,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load *trace_path*, verify it, and return an authoritative receipt dict.

    Parameters
    ----------
    trace_path:
        Path to the JSONL trace file produced by ``run_experiment.py``.
    config:
        Optional experiment configuration dict.  When *None*, basic structural
        verification is performed without config-level checks.
    """
    trace_path = Path(trace_path)
    events = load_trace(trace_path)

    if not events:
        return {
            "result": "FAIL",
            "reason": "empty_trace",
            "sha256_trace": hashlib.sha256(b"").hexdigest(),
            "crc16_trace": crc16_hex(b""),
        }

    # Structural check: required fields
    required_fields = {
        "ts", "trial_index", "symbol_index", "tx_bit", "rx_peak_mv",
        "decoded_bit", "threshold_mv", "symbol_pass",
    }
    for i, evt in enumerate(events):
        missing = required_fields - evt.keys()
        if missing:
            return {
                "result": "FAIL",
                "reason": f"missing_fields_event_{i}",
                "missing": sorted(missing),
            }

    effective_config = config or {
        "experiment_id": events[0].get("experiment_id", "unknown"),
    }

    receipt = build_receipt(effective_config, trace_path, events)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a blood-ion-repeat JSONL trace and emit a receipt."
    )
    parser.add_argument("trace", help="Path to the JSONL trace file.")
    parser.add_argument(
        "--config",
        help="Path to experiment config JSON (optional).",
        default=None,
    )
    parser.add_argument(
        "--receipt",
        help="Write the receipt JSON to this file (default: stdout).",
        default=None,
    )
    args = parser.parse_args(argv)

    config: dict[str, Any] | None = None
    if args.config:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    receipt = verify_trace(args.trace, config)

    receipt_json = json.dumps(receipt, indent=2)
    if args.receipt:
        Path(args.receipt).write_text(receipt_json + "\n", encoding="utf-8")
        print(f"Receipt written to {args.receipt}")
    else:
        print(receipt_json)

    return 0 if receipt.get("result") == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
