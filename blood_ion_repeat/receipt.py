"""Receipt generation for ionic channel experiment runs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical import canonical_json
from .crc16 import crc16_hex


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_receipt(
    config: dict[str, Any],
    trace_path: Path | str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a summary receipt for the completed experiment.

    Parameters
    ----------
    config:
        The experiment configuration dict.
    trace_path:
        Path to the JSONL trace file (used for hash computation).
    events:
        All trace events produced during the run.
    """
    trace_bytes = Path(trace_path).read_bytes()
    sha256_trace = _sha256_hex(trace_bytes)
    crc16_trace = crc16_hex(trace_bytes)

    total_symbols = len(events)
    symbol_errors = sum(
        1 for e in events if e.get("tx_bit") != e.get("decoded_bit")
    )
    ber = symbol_errors / total_symbols if total_symbols > 0 else 0.0

    # CRC pass: check each trial's frame independently
    trial_indices = sorted({e["trial_index"] for e in events})
    crc_pass_count = 0
    for ti in trial_indices:
        trial_events = [e for e in events if e["trial_index"] == ti]
        all_pass = all(e.get("symbol_pass", False) for e in trial_events)
        if all_pass:
            crc_pass_count += 1
    crc_pass_rate = crc_pass_count / len(trial_indices) if trial_indices else 0.0

    receipt: dict[str, Any] = {
        "experiment_id": config["experiment_id"],
        "result": "PASS" if symbol_errors == 0 else "FAIL",
        "trials": len(trial_indices),
        "symbols_total": total_symbols,
        "symbol_errors": symbol_errors,
        "ber": round(ber, 10),
        "crc_pass_rate": round(crc_pass_rate, 10),
        "sha256_trace": sha256_trace,
        "crc16_trace": crc16_trace,
    }
    return receipt
