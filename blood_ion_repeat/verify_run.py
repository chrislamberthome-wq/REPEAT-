"""CLI and logic for verifying a blood-ion-repeat experiment run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

from .replay import ReplaySummary, TrialVerifyRecord, replay_and_summarize

REQUIRED_CONFIG_FIELDS: List[str] = [
    "experiment_id",
    "channel_medium",
    "decode_threshold_mv",
    "trials",
]

REQUIRED_TRACE_FIELDS: List[str] = [
    "trial_index",
    "tx_bit",
    "rx_peak_mv",
]


def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate experiment configuration. Returns a list of error strings."""
    errors: List[str] = []
    for f in REQUIRED_CONFIG_FIELDS:
        if f not in config:
            errors.append(f"config missing required field: '{f}'")
    if "decode_threshold_mv" in config and not isinstance(
        config["decode_threshold_mv"], (int, float)
    ):
        errors.append("config field 'decode_threshold_mv' must be numeric")
    if "trials" in config and (
        not isinstance(config["trials"], int) or config["trials"] < 1
    ):
        errors.append("config field 'trials' must be a positive integer")
    return errors


def validate_trace_rows(rows: List[Dict[str, Any]]) -> List[str]:
    """Validate trace rows. Returns a list of error strings."""
    errors: List[str] = []
    if not rows:
        errors.append("trace is empty: no rows found")
        return errors
    for i, row in enumerate(rows):
        for f in REQUIRED_TRACE_FIELDS:
            if f not in row:
                errors.append(f"trace row {i} missing required field: '{f}'")
    return errors


def sha256_trace(rows: List[Dict[str, Any]]) -> str:
    """Compute a SHA-256 fingerprint of the canonical trace."""
    canonical = json.dumps(rows, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()


def load_config(path: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Load and parse a JSON config file. Returns ``(config, error_string)``."""
    try:
        with open(path) as fh:
            return json.load(fh), ""
    except FileNotFoundError:
        return None, f"config file not found: {path}"
    except json.JSONDecodeError as exc:
        return None, f"config file invalid JSON: {exc}"


def load_trace(path: str) -> Tuple[List[Dict[str, Any]], str]:
    """Load a JSONL trace file. Returns ``(rows, error_string)``."""
    rows: List[Dict[str, Any]] = []
    try:
        with open(path) as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    return [], f"trace line {lineno} invalid JSON: {exc}"
        return rows, ""
    except FileNotFoundError:
        return [], f"trace file not found: {path}"


def build_receipt(
    config: Dict[str, Any],
    summary: ReplaySummary,
    trace_hash: str,
) -> Dict[str, Any]:
    """Build a verification receipt dict from a :class:`ReplaySummary`."""
    trial_results = [
        {
            "trial_index": t.trial_index,
            "symbol_count": t.symbol_count,
            "symbol_errors": t.symbol_errors,
            "ber": t.ber,
            "crc_pass": t.crc_pass,
            "passed": t.passed,
            "fail_reason": t.fail_reason,
        }
        for t in summary.trials
    ]
    return {
        "schema": "blood-ion-repeat-verification-receipt-v1",
        "experiment_id": summary.experiment_id,
        "result": summary.result,
        "trial_count": summary.trial_count,
        "trials_passed": summary.trials_passed,
        "trials_failed": summary.trials_failed,
        "total_symbols": summary.total_symbols,
        "total_symbol_errors": summary.total_symbol_errors,
        "aggregate_ber": summary.aggregate_ber,
        "crc_pass_rate": summary.crc_pass_rate,
        "sha256_trace": trace_hash,
        "trial_results": trial_results,
    }


def run_verify(
    config_path: str,
    trace_path: str,
) -> Tuple[Dict[str, Any], int]:
    """Run full verification. Returns ``(receipt_dict, exit_code)``."""
    config, cfg_err = load_config(config_path)
    if cfg_err:
        return {"error": cfg_err}, 2

    cfg_errors = validate_config(config)  # type: ignore[arg-type]
    if cfg_errors:
        return {"errors": cfg_errors}, 2

    rows, trace_err = load_trace(trace_path)
    if trace_err:
        return {"error": trace_err}, 2

    trace_errors = validate_trace_rows(rows)
    if trace_errors:
        return {"errors": trace_errors}, 2

    trace_hash = sha256_trace(rows)
    summary = replay_and_summarize(rows, config)  # type: ignore[arg-type]
    receipt = build_receipt(config, summary, trace_hash)  # type: ignore[arg-type]
    exit_code = 0 if summary.result == "PASS" else 1
    return receipt, exit_code


def main() -> int:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description=(
            "blood-ion-repeat verify-run — verify a blood-ion-repeat "
            "experiment trace and produce an auditable receipt."
        )
    )
    parser.add_argument("config", help="Path to experiment config JSON file")
    parser.add_argument("trace", help="Path to trace JSONL file")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write receipt JSON to this file (default: stdout)",
    )
    args = parser.parse_args()

    receipt, exit_code = run_verify(args.config, args.trace)
    receipt_json = json.dumps(receipt, indent=2)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(receipt_json + "\n")
        print(f"Receipt written to {args.output}")
    else:
        print(receipt_json)

    status = receipt.get("result", "ERROR")
    print(f"Verification: {status}", file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
