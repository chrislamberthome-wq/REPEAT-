"""Tests for blood_ion_repeat.replay — trial grouping and multi-trial verification."""

from __future__ import annotations

import pytest

from blood_ion_repeat.replay import (
    ReplaySummary,
    TrialVerifyRecord,
    _crc16_ccitt_false,
    group_rows_by_trial,
    replay_and_summarize,
    verify_trial,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_row(trial_index: int, tx_bit: int, rx_peak_mv: float, symbol_index: int = 0) -> dict:
    return {
        "trial_index": trial_index,
        "symbol_index": symbol_index,
        "tx_bit": tx_bit,
        "rx_peak_mv": rx_peak_mv,
        "threshold_mv": 25.0,
    }


CLEAN_CONFIG = {
    "experiment_id": "test-exp-1",
    "channel_medium": "saline",
    "decode_threshold_mv": 25.0,
    "trials": 2,
}


# ---------------------------------------------------------------------------
# CRC helper
# ---------------------------------------------------------------------------

class TestCRC16:
    def test_known_empty(self):
        assert _crc16_ccitt_false(b"") == 0xFFFF

    def test_same_input_same_output(self):
        assert _crc16_ccitt_false(b"\x01\x00\x01") == _crc16_ccitt_false(b"\x01\x00\x01")

    def test_different_inputs_differ(self):
        assert _crc16_ccitt_false(b"\x01\x00") != _crc16_ccitt_false(b"\x00\x01")


# ---------------------------------------------------------------------------
# group_rows_by_trial
# ---------------------------------------------------------------------------

class TestGroupRowsByTrial:
    def test_single_trial(self):
        rows = [_make_row(0, 1, 30.0), _make_row(0, 0, 5.0)]
        grouped = group_rows_by_trial(rows)
        assert set(grouped.keys()) == {0}
        assert len(grouped[0]) == 2

    def test_multiple_trials(self):
        rows = [
            _make_row(0, 1, 30.0),
            _make_row(1, 0, 5.0),
            _make_row(2, 1, 28.0),
        ]
        grouped = group_rows_by_trial(rows)
        assert set(grouped.keys()) == {0, 1, 2}
        assert len(grouped[0]) == 1
        assert len(grouped[1]) == 1
        assert len(grouped[2]) == 1

    def test_empty_rows(self):
        assert group_rows_by_trial([]) == {}

    def test_preserves_row_order(self):
        rows = [
            _make_row(0, 1, 30.0, symbol_index=0),
            _make_row(0, 0, 5.0, symbol_index=1),
        ]
        grouped = group_rows_by_trial(rows)
        assert grouped[0][0]["symbol_index"] == 0
        assert grouped[0][1]["symbol_index"] == 1

    def test_missing_trial_index_defaults_to_zero(self):
        rows = [{"tx_bit": 1, "rx_peak_mv": 30.0}]
        grouped = group_rows_by_trial(rows)
        assert 0 in grouped


# ---------------------------------------------------------------------------
# verify_trial
# ---------------------------------------------------------------------------

class TestVerifyTrial:
    def test_all_correct_passes(self):
        rows = [
            _make_row(0, 1, 35.0),
            _make_row(0, 0, 5.0),
            _make_row(0, 1, 40.0),
        ]
        rec = verify_trial(0, rows, CLEAN_CONFIG)
        assert rec.passed is True
        assert rec.symbol_errors == 0
        assert rec.crc_pass is True
        assert rec.fail_reason == ""
        assert rec.ber == 0.0

    def test_symbol_error_fails(self):
        rows = [
            _make_row(0, 1, 5.0),   # tx=1 but rx below threshold → decoded=0 → error
            _make_row(0, 0, 5.0),
        ]
        rec = verify_trial(0, rows, CLEAN_CONFIG)
        assert rec.passed is False
        assert rec.symbol_errors == 1
        assert rec.fail_reason == "symbol_errors"

    def test_ber_calculation(self):
        rows = [_make_row(0, 1, 5.0)] * 4  # all errors
        rec = verify_trial(0, rows, CLEAN_CONFIG)
        assert rec.ber == 1.0

    def test_crc_pass_when_no_errors(self):
        rows = [_make_row(0, 1, 30.0), _make_row(0, 1, 30.0)]
        rec = verify_trial(0, rows, CLEAN_CONFIG)
        assert rec.crc_pass is True

    def test_trial_index_stored(self):
        rows = [_make_row(7, 0, 5.0)]
        rec = verify_trial(7, rows, CLEAN_CONFIG)
        assert rec.trial_index == 7


# ---------------------------------------------------------------------------
# replay_and_summarize
# ---------------------------------------------------------------------------

class TestReplayAndSummarize:
    def _clean_rows(self, num_trials: int = 3, symbols_per_trial: int = 4) -> list:
        rows = []
        for t in range(num_trials):
            for s in range(symbols_per_trial):
                rows.append(_make_row(t, 1, 35.0, symbol_index=s))
        return rows

    def test_all_pass(self):
        rows = self._clean_rows(num_trials=3)
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert summary.result == "PASS"
        assert summary.trial_count == 3
        assert summary.trials_passed == 3
        assert summary.trials_failed == 0
        assert summary.aggregate_ber == 0.0
        assert summary.crc_pass_rate == 1.0

    def test_one_failing_trial(self):
        rows = self._clean_rows(num_trials=2)
        # Inject an error into trial 1 by replacing one row
        rows.append(_make_row(2, 1, 5.0))  # decoded=0, error
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert summary.result == "FAIL"
        assert summary.trials_failed == 1
        assert summary.trials_passed == 2

    def test_experiment_id_propagated(self):
        rows = self._clean_rows(num_trials=1)
        cfg = dict(CLEAN_CONFIG, experiment_id="my-exp")
        summary = replay_and_summarize(rows, cfg)
        assert summary.experiment_id == "my-exp"

    def test_total_symbols_correct(self):
        rows = self._clean_rows(num_trials=3, symbols_per_trial=4)
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert summary.total_symbols == 12

    def test_returns_replay_summary_type(self):
        rows = self._clean_rows(num_trials=1)
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert isinstance(summary, ReplaySummary)

    def test_trial_records_populated(self):
        rows = self._clean_rows(num_trials=2)
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert len(summary.trials) == 2
        for t in summary.trials:
            assert isinstance(t, TrialVerifyRecord)

    def test_empty_rows(self):
        summary = replay_and_summarize([], CLEAN_CONFIG)
        assert summary.trial_count == 0
        assert summary.result == "FAIL"  # no trials → cannot pass
        assert summary.aggregate_ber == 0.0

    def test_aggregate_ber_partial_errors(self):
        # 2 symbols in trial 0: one error
        rows = [_make_row(0, 1, 35.0), _make_row(0, 1, 5.0)]
        summary = replay_and_summarize(rows, CLEAN_CONFIG)
        assert summary.total_symbol_errors == 1
        assert summary.aggregate_ber == pytest.approx(0.5)
