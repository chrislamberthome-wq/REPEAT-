"""Tests for blood_ion_repeat.verify_run — config/trace validation, receipt generation."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List

import pytest

from blood_ion_repeat.verify_run import (
    build_receipt,
    load_config,
    load_trace,
    run_verify,
    sha256_trace,
    validate_config,
    validate_trace_rows,
)
from blood_ion_repeat.replay import replay_and_summarize


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_CONFIG: Dict[str, Any] = {
    "experiment_id": "test-hydrogel-v1",
    "channel_medium": "saline hydrogel",
    "decode_threshold_mv": 20.0,
    "trials": 3,
}


def _make_trace_rows(num_trials: int = 2, symbols: int = 4, threshold: float = 20.0) -> List[Dict[str, Any]]:
    """Generate a valid, error-free multi-trial trace."""
    rows = []
    for t in range(num_trials):
        for s in range(symbols):
            tx_bit = s % 2
            rx_peak = 35.0 if tx_bit == 1 else 5.0
            rows.append({
                "trial_index": t,
                "symbol_index": s,
                "tx_bit": tx_bit,
                "rx_peak_mv": rx_peak,
                "threshold_mv": threshold,
            })
    return rows


def _write_jsonl(rows: List[Dict[str, Any]]) -> str:
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for row in rows:
        fh.write(json.dumps(row) + "\n")
    fh.close()
    return fh.name


def _write_json(obj: Dict[str, Any]) -> str:
    fh = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(obj, fh)
    fh.close()
    return fh.name


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

class TestValidateConfig:
    def test_valid_config_no_errors(self):
        assert validate_config(VALID_CONFIG) == []

    def test_missing_experiment_id(self):
        cfg = {k: v for k, v in VALID_CONFIG.items() if k != "experiment_id"}
        errors = validate_config(cfg)
        assert any("experiment_id" in e for e in errors)

    def test_missing_channel_medium(self):
        cfg = {k: v for k, v in VALID_CONFIG.items() if k != "channel_medium"}
        errors = validate_config(cfg)
        assert any("channel_medium" in e for e in errors)

    def test_missing_threshold(self):
        cfg = {k: v for k, v in VALID_CONFIG.items() if k != "decode_threshold_mv"}
        errors = validate_config(cfg)
        assert any("decode_threshold_mv" in e for e in errors)

    def test_missing_trials(self):
        cfg = {k: v for k, v in VALID_CONFIG.items() if k != "trials"}
        errors = validate_config(cfg)
        assert any("trials" in e for e in errors)

    def test_non_numeric_threshold_fails(self):
        cfg = dict(VALID_CONFIG, decode_threshold_mv="bad")
        errors = validate_config(cfg)
        assert any("decode_threshold_mv" in e for e in errors)

    def test_zero_trials_fails(self):
        cfg = dict(VALID_CONFIG, trials=0)
        errors = validate_config(cfg)
        assert any("trials" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_trace_rows
# ---------------------------------------------------------------------------

class TestValidateTraceRows:
    def test_valid_rows_no_errors(self):
        rows = _make_trace_rows()
        assert validate_trace_rows(rows) == []

    def test_empty_rows_error(self):
        errors = validate_trace_rows([])
        assert any("empty" in e for e in errors)

    def test_missing_trial_index(self):
        rows = [{"tx_bit": 1, "rx_peak_mv": 30.0}]
        errors = validate_trace_rows(rows)
        assert any("trial_index" in e for e in errors)

    def test_missing_tx_bit(self):
        rows = [{"trial_index": 0, "rx_peak_mv": 30.0}]
        errors = validate_trace_rows(rows)
        assert any("tx_bit" in e for e in errors)

    def test_missing_rx_peak_mv(self):
        rows = [{"trial_index": 0, "tx_bit": 1}]
        errors = validate_trace_rows(rows)
        assert any("rx_peak_mv" in e for e in errors)


# ---------------------------------------------------------------------------
# sha256_trace
# ---------------------------------------------------------------------------

class TestSha256Trace:
    def test_returns_sha256_prefix(self):
        h = sha256_trace([{"x": 1}])
        assert h.startswith("sha256:")
        assert len(h) == 7 + 64

    def test_deterministic(self):
        rows = _make_trace_rows()
        assert sha256_trace(rows) == sha256_trace(rows)

    def test_different_rows_different_hash(self):
        rows1 = [{"trial_index": 0, "tx_bit": 1, "rx_peak_mv": 30.0}]
        rows2 = [{"trial_index": 0, "tx_bit": 0, "rx_peak_mv": 5.0}]
        assert sha256_trace(rows1) != sha256_trace(rows2)


# ---------------------------------------------------------------------------
# load_config / load_trace
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_loads_valid_json(self):
        path = _write_json(VALID_CONFIG)
        try:
            cfg, err = load_config(path)
            assert err == ""
            assert cfg == VALID_CONFIG
        finally:
            os.unlink(path)

    def test_missing_file_returns_error(self):
        cfg, err = load_config("/nonexistent/path/config.json")
        assert cfg is None
        assert "not found" in err

    def test_invalid_json_returns_error(self):
        fh = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        fh.write("{bad json}")
        fh.close()
        try:
            cfg, err = load_config(fh.name)
            assert cfg is None
            assert "invalid JSON" in err
        finally:
            os.unlink(fh.name)


class TestLoadTrace:
    def test_loads_valid_jsonl(self):
        rows = _make_trace_rows()
        path = _write_jsonl(rows)
        try:
            loaded, err = load_trace(path)
            assert err == ""
            assert len(loaded) == len(rows)
        finally:
            os.unlink(path)

    def test_missing_file_returns_error(self):
        rows, err = load_trace("/nonexistent/path/trace.jsonl")
        assert rows == []
        assert "not found" in err

    def test_invalid_jsonl_returns_error(self):
        fh = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        fh.write("{bad json}\n")
        fh.close()
        try:
            rows, err = load_trace(fh.name)
            assert rows == []
            assert "invalid JSON" in err
        finally:
            os.unlink(fh.name)

    def test_skips_blank_lines(self):
        fh = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        fh.write('{"trial_index": 0, "tx_bit": 1, "rx_peak_mv": 30.0}\n')
        fh.write("\n")
        fh.write('{"trial_index": 0, "tx_bit": 0, "rx_peak_mv": 5.0}\n')
        fh.close()
        try:
            rows, err = load_trace(fh.name)
            assert err == ""
            assert len(rows) == 2
        finally:
            os.unlink(fh.name)


# ---------------------------------------------------------------------------
# build_receipt
# ---------------------------------------------------------------------------

class TestBuildReceipt:
    def _make_summary(self):
        rows = _make_trace_rows(num_trials=2)
        return replay_and_summarize(rows, VALID_CONFIG)

    def test_receipt_schema(self):
        summary = self._make_summary()
        receipt = build_receipt(VALID_CONFIG, summary, "sha256:" + "a" * 64)
        assert receipt["schema"] == "blood-ion-repeat-verification-receipt-v1"

    def test_receipt_has_required_fields(self):
        summary = self._make_summary()
        receipt = build_receipt(VALID_CONFIG, summary, "sha256:" + "a" * 64)
        for field in ("experiment_id", "result", "trial_count", "trials_passed",
                      "trials_failed", "aggregate_ber", "crc_pass_rate",
                      "sha256_trace", "trial_results"):
            assert field in receipt, f"missing field: {field}"

    def test_trial_results_list(self):
        summary = self._make_summary()
        receipt = build_receipt(VALID_CONFIG, summary, "sha256:" + "a" * 64)
        assert isinstance(receipt["trial_results"], list)
        assert len(receipt["trial_results"]) == 2

    def test_trial_result_fields(self):
        summary = self._make_summary()
        receipt = build_receipt(VALID_CONFIG, summary, "sha256:" + "a" * 64)
        tr = receipt["trial_results"][0]
        for field in ("trial_index", "symbol_count", "symbol_errors", "ber",
                      "crc_pass", "passed", "fail_reason"):
            assert field in tr


# ---------------------------------------------------------------------------
# run_verify (integration)
# ---------------------------------------------------------------------------

class TestRunVerify:
    def test_passing_run(self):
        cfg_path = _write_json(VALID_CONFIG)
        rows = _make_trace_rows(num_trials=3, threshold=20.0)
        trace_path = _write_jsonl(rows)
        try:
            receipt, code = run_verify(cfg_path, trace_path)
            assert code == 0
            assert receipt["result"] == "PASS"
            assert receipt["trial_count"] == 3
            assert receipt["trials_failed"] == 0
        finally:
            os.unlink(cfg_path)
            os.unlink(trace_path)

    def test_failing_run_returns_code_1(self):
        # Use threshold so high that all rx_peak fail
        cfg = dict(VALID_CONFIG, decode_threshold_mv=999.0)
        cfg_path = _write_json(cfg)
        rows = _make_trace_rows(num_trials=2)
        trace_path = _write_jsonl(rows)
        try:
            receipt, code = run_verify(cfg_path, trace_path)
            assert code == 1
            assert receipt["result"] == "FAIL"
        finally:
            os.unlink(cfg_path)
            os.unlink(trace_path)

    def test_missing_config_returns_code_2(self):
        _, code = run_verify("/nonexistent/config.json", "/nonexistent/trace.jsonl")
        assert code == 2

    def test_missing_trace_returns_code_2(self):
        cfg_path = _write_json(VALID_CONFIG)
        try:
            _, code = run_verify(cfg_path, "/nonexistent/trace.jsonl")
            assert code == 2
        finally:
            os.unlink(cfg_path)

    def test_invalid_config_returns_code_2(self):
        bad_cfg = {"experiment_id": "only-this-field"}
        cfg_path = _write_json(bad_cfg)
        rows = _make_trace_rows()
        trace_path = _write_jsonl(rows)
        try:
            receipt, code = run_verify(cfg_path, trace_path)
            assert code == 2
            assert "errors" in receipt
        finally:
            os.unlink(cfg_path)
            os.unlink(trace_path)

    def test_empty_trace_returns_code_2(self):
        cfg_path = _write_json(VALID_CONFIG)
        fh = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        fh.close()
        try:
            receipt, code = run_verify(cfg_path, fh.name)
            assert code == 2
        finally:
            os.unlink(cfg_path)
            os.unlink(fh.name)

    def test_receipt_sha256_trace_format(self):
        cfg_path = _write_json(VALID_CONFIG)
        rows = _make_trace_rows()
        trace_path = _write_jsonl(rows)
        try:
            receipt, _ = run_verify(cfg_path, trace_path)
            assert receipt["sha256_trace"].startswith("sha256:")
            assert len(receipt["sha256_trace"]) == 71
        finally:
            os.unlink(cfg_path)
            os.unlink(trace_path)

    def test_multi_trial_receipt_structure(self):
        cfg_path = _write_json(VALID_CONFIG)
        rows = _make_trace_rows(num_trials=3, symbols=6)
        trace_path = _write_jsonl(rows)
        try:
            receipt, code = run_verify(cfg_path, trace_path)
            assert code == 0
            assert receipt["trial_count"] == 3
            assert receipt["total_symbols"] == 18
            assert len(receipt["trial_results"]) == 3
        finally:
            os.unlink(cfg_path)
            os.unlink(trace_path)
