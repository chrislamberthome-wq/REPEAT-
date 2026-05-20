"""Tests for blood_ion_repeat.run_experiment: multi-trial traces, deterministic
timestamps, and round-trip verification.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from blood_ion_repeat.run_experiment import run_experiment, _frame_bits
from blood_ion_repeat.trace import load_trace
from blood_ion_repeat.verifier import verify_trace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "experiment_id": "test-run",
    "channel_medium": "0.9% saline",
    "electrode_type": "inert_baseline",
    "electrode_spacing_mm": 20,
    "pulse_voltage_v": 0.2,
    "pulse_width_ms": 100,
    "symbol_period_ms": 500,
    "preamble_bits": "1010",
    "payload_bits": "11001100",
    "crc_mode": "CRC-16/CCITT-FALSE",
    "decode_threshold_mv": 25.0,
    "trials": 3,
    "timestamp_seed_utc": "2026-04-02T12:00:00Z",
    "trial_spacing_seconds": 60,
    "symbol_spacing_seconds": 1,
}

MULTITRIAL_CONFIG = {
    **MINIMAL_CONFIG,
    "noise_schedule_mv": [0.0, -10.0, -30.0],
}


def _run_to_tmp(config: dict, seed: int = 42) -> tuple[Path, dict]:
    """Run experiment to a temp file and return (trace_path, receipt)."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        trace_path = Path(f.name)
    receipt = run_experiment(config, trace_path, rng_seed=seed)
    return trace_path, receipt


# ---------------------------------------------------------------------------
# Multi-trial trace generation
# ---------------------------------------------------------------------------

class TestMultiTrialTraceGeneration:
    def test_correct_number_of_trials(self):
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG)
        try:
            events = load_trace(trace_path)
            trial_indices = {e["trial_index"] for e in events}
            assert trial_indices == {0, 1, 2}
        finally:
            trace_path.unlink(missing_ok=True)

    def test_symbols_per_trial(self):
        """Each trial should contain exactly len(frame_bits) symbol events."""
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG)
        try:
            events = load_trace(trace_path)
            frame = _frame_bits(
                MINIMAL_CONFIG["preamble_bits"],
                MINIMAL_CONFIG["payload_bits"],
                MINIMAL_CONFIG["crc_mode"],
            )
            expected_per_trial = len(frame)
            for ti in range(MINIMAL_CONFIG["trials"]):
                trial_events = [e for e in events if e["trial_index"] == ti]
                assert len(trial_events) == expected_per_trial, (
                    f"Trial {ti}: expected {expected_per_trial} symbols, got {len(trial_events)}"
                )
        finally:
            trace_path.unlink(missing_ok=True)

    def test_total_event_count(self):
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG)
        try:
            events = load_trace(trace_path)
            frame = _frame_bits(
                MINIMAL_CONFIG["preamble_bits"],
                MINIMAL_CONFIG["payload_bits"],
                MINIMAL_CONFIG["crc_mode"],
            )
            assert len(events) == MINIMAL_CONFIG["trials"] * len(frame)
        finally:
            trace_path.unlink(missing_ok=True)

    def test_required_fields_present(self):
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG)
        try:
            events = load_trace(trace_path)
            required = {
                "ts", "trial_index", "symbol_index", "tx_bit",
                "pulse_voltage_v", "pulse_width_ms", "rx_peak_mv",
                "rx_settle_ms", "decoded_bit", "threshold_mv", "symbol_pass",
            }
            for evt in events:
                missing = required - evt.keys()
                assert not missing, f"Missing fields: {missing}"
        finally:
            trace_path.unlink(missing_ok=True)

    def test_noise_schedule_affects_rx_peak(self):
        """Trials with lower noise should show smaller variance in rx_peak_mv."""
        config = {**MULTITRIAL_CONFIG, "trials": 3}
        trace_path, _ = _run_to_tmp(config, seed=0)
        try:
            events = load_trace(trace_path)

            def variance(vals: list[float]) -> float:
                if len(vals) < 2:
                    return 0.0
                mean = sum(vals) / len(vals)
                return sum((v - mean) ** 2 for v in vals) / len(vals)

            # Collect rx_peak for '1' bits per trial
            peaks: dict[int, list[float]] = {0: [], 1: [], 2: []}
            for e in events:
                if e["tx_bit"] == 1:
                    peaks[e["trial_index"]].append(e["rx_peak_mv"])

            # Trial 2 has noise_schedule_mv=-30 → noise_std ≈ 0; much lower variance
            var0 = variance(peaks[0])
            var2 = variance(peaks[2])
            assert var2 <= var0, (
                f"Trial 2 (low noise) variance {var2:.4f} should be <= trial 0 variance {var0:.4f}"
            )
        finally:
            trace_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Deterministic timestamps
# ---------------------------------------------------------------------------

class TestDeterministicTimestamps:
    def test_seed_produces_fixed_first_ts(self):
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG, seed=1)
        try:
            events = load_trace(trace_path)
            assert events[0]["ts"] == "2026-04-02T12:00:00Z"
        finally:
            trace_path.unlink(missing_ok=True)

    def test_trial_spacing_applied(self):
        """Second trial should start trial_spacing_seconds after the first."""
        config = {**MINIMAL_CONFIG, "trial_spacing_seconds": 60}
        trace_path, _ = _run_to_tmp(config, seed=1)
        try:
            events = load_trace(trace_path)
            trial0_ts = events[0]["ts"]
            trial1_first = next(e for e in events if e["trial_index"] == 1)["ts"]
            assert trial1_first == "2026-04-02T12:01:00Z", (
                f"Expected second trial at 12:01:00, got {trial1_first}"
            )
        finally:
            trace_path.unlink(missing_ok=True)

    def test_symbol_spacing_applied(self):
        """Consecutive symbols within a trial differ by symbol_spacing_seconds."""
        config = {**MINIMAL_CONFIG, "symbol_spacing_seconds": 1}
        trace_path, _ = _run_to_tmp(config, seed=1)
        try:
            events = load_trace(trace_path)
            trial0_events = [e for e in events if e["trial_index"] == 0]
            ts0 = trial0_events[0]["ts"]
            ts1 = trial0_events[1]["ts"]
            assert ts0 == "2026-04-02T12:00:00Z"
            assert ts1 == "2026-04-02T12:00:01Z"
        finally:
            trace_path.unlink(missing_ok=True)

    def test_same_seed_same_timestamps(self):
        trace1, _ = _run_to_tmp(MINIMAL_CONFIG, seed=99)
        trace2, _ = _run_to_tmp(MINIMAL_CONFIG, seed=99)
        try:
            e1 = load_trace(trace1)
            e2 = load_trace(trace2)
            ts1 = [e["ts"] for e in e1]
            ts2 = [e["ts"] for e in e2]
            assert ts1 == ts2
        finally:
            trace1.unlink(missing_ok=True)
            trace2.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Deterministic RNG (full trace equality)
# ---------------------------------------------------------------------------

class TestDeterministicRNG:
    def test_same_seed_same_trace(self):
        trace1, receipt1 = _run_to_tmp(MINIMAL_CONFIG, seed=42)
        trace2, receipt2 = _run_to_tmp(MINIMAL_CONFIG, seed=42)
        try:
            assert load_trace(trace1) == load_trace(trace2)
        finally:
            trace1.unlink(missing_ok=True)
            trace2.unlink(missing_ok=True)

    def test_different_seeds_different_trace(self):
        trace1, _ = _run_to_tmp(MINIMAL_CONFIG, seed=1)
        trace2, _ = _run_to_tmp(MINIMAL_CONFIG, seed=2)
        try:
            events1 = load_trace(trace1)
            events2 = load_trace(trace2)
            rx_peaks1 = [e["rx_peak_mv"] for e in events1]
            rx_peaks2 = [e["rx_peak_mv"] for e in events2]
            assert rx_peaks1 != rx_peaks2
        finally:
            trace1.unlink(missing_ok=True)
            trace2.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Round-trip verification
# ---------------------------------------------------------------------------

class TestRoundTripVerification:
    def test_verify_passes_for_high_snr(self):
        """With very low noise and a clear threshold, the verifier should pass."""
        config = {
            **MINIMAL_CONFIG,
            "noise_schedule_mv": [-100.0, -100.0, -100.0],  # near-zero noise
        }
        trace_path, _ = _run_to_tmp(config, seed=42)
        try:
            receipt = verify_trace(trace_path, config)
            assert receipt["result"] == "PASS", f"Expected PASS, got: {receipt}"
        finally:
            trace_path.unlink(missing_ok=True)

    def test_verify_trace_structural_ok(self):
        trace_path, _ = _run_to_tmp(MINIMAL_CONFIG, seed=0)
        try:
            receipt = verify_trace(trace_path)
            assert "result" in receipt
            assert "sha256_trace" in receipt
            assert "crc16_trace" in receipt
        finally:
            trace_path.unlink(missing_ok=True)

    def test_provisional_and_authoritative_receipts_consistent(self):
        """The provisional receipt from run_experiment and the authoritative
        receipt from verify_trace should agree on sha256_trace."""
        trace_path, prov_receipt = _run_to_tmp(MINIMAL_CONFIG, seed=5)
        try:
            auth_receipt = verify_trace(trace_path, MINIMAL_CONFIG)
            assert prov_receipt["sha256_trace"] == auth_receipt["sha256_trace"]
        finally:
            trace_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Frame bits helper
# ---------------------------------------------------------------------------

class TestFrameBits:
    def test_length(self):
        frame = _frame_bits("1010", "11001100", "CRC-16/CCITT-FALSE")
        # preamble(4) + payload(8) + CRC-16(16) = 28
        assert len(frame) == 28

    def test_starts_with_preamble(self):
        frame = _frame_bits("1010", "11001100", "CRC-16/CCITT-FALSE")
        assert frame.startswith("1010")

    def test_deterministic(self):
        f1 = _frame_bits("1010", "11001100", "CRC-16/CCITT-FALSE")
        f2 = _frame_bits("1010", "11001100", "CRC-16/CCITT-FALSE")
        assert f1 == f2
