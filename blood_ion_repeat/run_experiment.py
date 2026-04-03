"""Multi-trial ionic channel experiment runner.

This script is a *trace generator* and *provisional receipt emitter*.
The authoritative verifier is ``blood_ion_repeat.verifier`` (``verify_run.py``).

Usage::

    python -m blood_ion_repeat.run_experiment --config <config.json> \\
        [--trace <out.jsonl>] [--receipt <out.json>] [--seed <int>]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .channel_model import ChannelParams, default_params, params_for_trial, simulate_symbol
from .crc16 import crc16_ccitt_false
from .receipt import build_receipt
from .thresholds import ThresholdConfig
from .trace import TraceWriter


def _parse_timestamp_seed(ts_str: str) -> datetime:
    """Parse an ISO-8601 UTC timestamp string into a timezone-aware datetime."""
    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def _bits_to_bytes(bits: str) -> bytes:
    """Convert a string of '0'/'1' characters to bytes (left-padded to byte boundary)."""
    padded = bits.zfill((len(bits) + 7) // 8 * 8)
    return bytes(int(padded[i:i+8], 2) for i in range(0, len(padded), 8))


def _frame_bits(preamble: str, payload: str, crc_mode: str) -> str:
    """Return the complete frame bit string: preamble + payload + CRC-16."""
    payload_bytes = _bits_to_bytes(payload)
    crc_val = crc16_ccitt_false(payload_bytes)
    crc_bits = f"{crc_val:016b}"
    return preamble + payload + crc_bits


def run_experiment(
    config: dict[str, Any],
    trace_path: Path | str,
    rng_seed: int | None = None,
) -> dict[str, Any]:
    """Execute the multi-trial experiment defined by *config*.

    Parameters
    ----------
    config:
        Validated experiment configuration dictionary.
    trace_path:
        Destination JSONL file for the trace.
    rng_seed:
        Optional integer seed for the random number generator (overrides any
        seed embedded in *config*).  When *None* and no seed is present in the
        config, a non-deterministic run is performed.

    Returns
    -------
    dict
        Provisional receipt.  Use ``verifier.verify_trace`` for the
        authoritative receipt.
    """
    trace_path = Path(trace_path)

    # --- RNG setup ---
    rng = random.Random(rng_seed)

    # --- Timing setup ---
    trial_spacing = float(config.get("trial_spacing_seconds", 60))
    symbol_spacing = float(config.get("symbol_spacing_seconds", 1))

    use_seed_ts = "timestamp_seed_utc" in config and config["timestamp_seed_utc"]
    if use_seed_ts:
        base_ts = _parse_timestamp_seed(config["timestamp_seed_utc"])
    else:
        base_ts = datetime.now(tz=timezone.utc)

    # --- Channel parameters ---
    base_params = default_params()
    noise_schedule: list[float] | None = config.get("noise_schedule_mv") or None

    # --- Threshold ---
    threshold_cfg = ThresholdConfig(
        threshold_mv=float(config["decode_threshold_mv"]),
        baseline_mv=base_params.baseline_mv,
    )

    # --- Frame construction ---
    frame_bits = _frame_bits(
        config["preamble_bits"],
        config["payload_bits"],
        config["crc_mode"],
    )

    n_trials = int(config["trials"])
    all_events: list[dict[str, Any]] = []

    with TraceWriter(trace_path) as writer:
        for trial_idx in range(n_trials):
            trial_params = params_for_trial(base_params, trial_idx, noise_schedule)
            trial_start = base_ts + timedelta(seconds=trial_idx * trial_spacing)

            for sym_idx, bit_char in enumerate(frame_bits):
                tx_bit = int(bit_char)

                sym_ts = trial_start + timedelta(seconds=sym_idx * symbol_spacing)
                ts_str = sym_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

                measurement = simulate_symbol(
                    tx_bit=tx_bit,
                    pulse_voltage_v=float(config["pulse_voltage_v"]),
                    pulse_width_ms=float(config["pulse_width_ms"]),
                    params=trial_params,
                    rng=rng,
                )

                decoded_bit = threshold_cfg.decode(measurement["rx_peak_mv"])
                symbol_pass = decoded_bit == tx_bit

                event: dict[str, Any] = {
                    "ts": ts_str,
                    "trial_index": trial_idx,
                    "symbol_index": sym_idx,
                    "tx_bit": tx_bit,
                    "pulse_voltage_v": float(config["pulse_voltage_v"]),
                    "pulse_width_ms": float(config["pulse_width_ms"]),
                    "rx_peak_mv": measurement["rx_peak_mv"],
                    "rx_settle_ms": measurement["rx_settle_ms"],
                    "decoded_bit": decoded_bit,
                    "threshold_mv": threshold_cfg.threshold_mv,
                    "symbol_pass": symbol_pass,
                }
                writer.write(event)
                all_events.append(event)

    receipt = build_receipt(config, trace_path, all_events)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a multi-trial ionic channel experiment and emit a JSONL trace. "
            "Use verify_run.py for authoritative verification."
        )
    )
    parser.add_argument("--config", required=True, help="Path to experiment config JSON.")
    parser.add_argument(
        "--trace",
        default="trace.jsonl",
        help="Output path for the JSONL trace (default: trace.jsonl).",
    )
    parser.add_argument(
        "--receipt",
        default=None,
        help="Write provisional receipt JSON to this file (default: stdout).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Integer seed for the RNG (overrides config).",
    )
    args = parser.parse_args(argv)

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))

    receipt = run_experiment(config, args.trace, rng_seed=args.seed)

    receipt_json = json.dumps(receipt, indent=2)
    if args.receipt:
        Path(args.receipt).write_text(receipt_json + "\n", encoding="utf-8")
        print(f"Provisional receipt written to {args.receipt}")
    else:
        print(receipt_json)

    print(f"Trace written to {args.trace}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
