"""Multi-trial replay and verification for blood-ion-repeat experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class TrialVerifyRecord:
    """Verification record for a single trial."""

    trial_index: int
    symbol_count: int
    symbol_errors: int
    ber: float
    crc_pass: bool
    passed: bool
    fail_reason: str = ""


@dataclass
class ReplaySummary:
    """Aggregated verification summary across all trials."""

    experiment_id: str
    trial_count: int
    trials_passed: int
    trials_failed: int
    total_symbols: int
    total_symbol_errors: int
    aggregate_ber: float
    crc_pass_rate: float
    result: str  # "PASS" or "FAIL"
    trials: List[TrialVerifyRecord] = field(default_factory=list)


def _crc16_ccitt_false(data: bytes) -> int:
    """Compute CRC-16/CCITT-FALSE (poly=0x1021, init=0xFFFF, refin=False)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


def group_rows_by_trial(
    rows: List[Dict[str, Any]],
) -> Dict[int, List[Dict[str, Any]]]:
    """Group trace rows by their ``trial_index`` field."""
    trials: Dict[int, List[Dict[str, Any]]] = {}
    for row in rows:
        tidx = int(row.get("trial_index", 0))
        trials.setdefault(tidx, []).append(row)
    return trials


def verify_trial(
    trial_index: int,
    rows: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> TrialVerifyRecord:
    """Verify a single trial from its trace rows against *config*.

    Decoding rule: decoded_bit = 1 iff ``rx_peak_mv`` >= ``decode_threshold_mv``.
    CRC check: CRC-16/CCITT-FALSE over the transmitted bit sequence must equal
    CRC-16/CCITT-FALSE over the decoded bit sequence.
    """
    threshold_mv: float = float(config.get("decode_threshold_mv", 25.0))
    symbol_count = len(rows)
    symbol_errors = 0

    tx_bits_list: List[int] = []
    decoded_bits_list: List[int] = []

    for row in rows:
        tx_bit = int(row.get("tx_bit", 0))
        rx_peak_mv = float(row.get("rx_peak_mv", 0.0))
        decoded_bit = 1 if rx_peak_mv >= threshold_mv else 0
        tx_bits_list.append(tx_bit)
        decoded_bits_list.append(decoded_bit)
        if decoded_bit != tx_bit:
            symbol_errors += 1

    ber = symbol_errors / symbol_count if symbol_count > 0 else 0.0

    tx_crc = _crc16_ccitt_false(bytes(tx_bits_list))
    decoded_crc = _crc16_ccitt_false(bytes(decoded_bits_list))
    crc_pass = tx_crc == decoded_crc

    passed = symbol_errors == 0 and crc_pass
    fail_reason = ""
    if symbol_errors > 0:
        fail_reason = "symbol_errors"
    elif not crc_pass:
        fail_reason = "crc_mismatch"

    return TrialVerifyRecord(
        trial_index=trial_index,
        symbol_count=symbol_count,
        symbol_errors=symbol_errors,
        ber=ber,
        crc_pass=crc_pass,
        passed=passed,
        fail_reason=fail_reason,
    )


def replay_and_summarize(
    rows: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> ReplaySummary:
    """Replay *rows* grouped by trial and produce an aggregated summary."""
    experiment_id: str = str(config.get("experiment_id", "unknown"))
    grouped = group_rows_by_trial(rows)

    trial_records: List[TrialVerifyRecord] = [
        verify_trial(tidx, grouped[tidx], config)
        for tidx in sorted(grouped.keys())
    ]

    trial_count = len(trial_records)
    trials_passed = sum(1 for r in trial_records if r.passed)
    trials_failed = trial_count - trials_passed
    total_symbols = sum(r.symbol_count for r in trial_records)
    total_symbol_errors = sum(r.symbol_errors for r in trial_records)
    aggregate_ber = (
        total_symbol_errors / total_symbols if total_symbols > 0 else 0.0
    )
    crc_pass_count = sum(1 for r in trial_records if r.crc_pass)
    crc_pass_rate = crc_pass_count / trial_count if trial_count > 0 else 0.0
    result = "PASS" if trial_count > 0 and trials_failed == 0 else "FAIL"

    return ReplaySummary(
        experiment_id=experiment_id,
        trial_count=trial_count,
        trials_passed=trials_passed,
        trials_failed=trials_failed,
        total_symbols=total_symbols,
        total_symbol_errors=total_symbol_errors,
        aggregate_ber=aggregate_ber,
        crc_pass_rate=crc_pass_rate,
        result=result,
        trials=trial_records,
    )
