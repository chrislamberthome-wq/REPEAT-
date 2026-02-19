"""Tests for the GAD_FLY B4IU v0.1 verifier."""

import json
import pytest
from verifier.gad_fly import verify_trial, verify_trial_json, B4IU_ID


class TestVerifyTrialPass:
    """Cases that should produce a PASS verdict (C == 1)."""

    def test_correct_bit_within_deadline(self):
        """Correct rx_bit, response within t_max_ms → PASS."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500)
        assert result["verdict"] == "PASS"
        assert result["delta"] == 1
        assert result["P"] == 0
        assert result["C"] == 1

    def test_correct_zero_bit(self):
        """tx_bit=0, rx_bit=0, well within deadline → PASS."""
        result = verify_trial(tx_bit=0, rx_bit=0, rt_ms=100, t_max_ms=1500)
        assert result["verdict"] == "PASS"

    def test_response_exactly_at_deadline(self):
        """rt_ms == t_max_ms is not strictly greater, so no time penalty → PASS."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=1500, t_max_ms=1500)
        assert result["verdict"] == "PASS"
        assert result["P"] == 0


class TestVerifyTrialFail:
    """Cases that should produce a FAIL verdict."""

    def test_wrong_bit(self):
        """rx_bit differs from tx_bit → delta=0 → FAIL."""
        result = verify_trial(tx_bit=1, rx_bit=0, rt_ms=200, t_max_ms=1500)
        assert result["verdict"] == "FAIL"
        assert result["delta"] == 0
        assert result["P"] == 0
        assert result["C"] == 0

    def test_response_time_exceeded(self):
        """rt_ms > t_max_ms → P=1 → FAIL even with correct bit."""
        result = verify_trial(tx_bit=0, rx_bit=0, rt_ms=1501, t_max_ms=1500)
        assert result["verdict"] == "FAIL"
        assert result["P"] == 1
        assert result["C"] == 0

    def test_panic_flag(self):
        """panic=1 → P=1 → FAIL even with correct bit and fast response."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=300, t_max_ms=1500, panic=1)
        assert result["verdict"] == "FAIL"
        assert result["P"] == 1

    def test_invalid_response(self):
        """invalid_response=True → P=1 → FAIL."""
        result = verify_trial(
            tx_bit=0, rx_bit=0, rt_ms=200, t_max_ms=1500, invalid_response=True
        )
        assert result["verdict"] == "FAIL"
        assert result["P"] == 1

    def test_timeout_and_wrong_bit(self):
        """Both wrong bit and timeout: delta=0, P=1, C=-1 → FAIL."""
        result = verify_trial(tx_bit=1, rx_bit=0, rt_ms=2000, t_max_ms=1500)
        assert result["verdict"] == "FAIL"
        assert result["delta"] == 0
        assert result["P"] == 1
        assert result["C"] == -1

    def test_panic_overrides_correct_response(self):
        """Panic=1 overrides a correct, timely response → FAIL."""
        result = verify_trial(tx_bit=0, rx_bit=0, rt_ms=50, t_max_ms=1500, panic=1)
        assert result["verdict"] == "FAIL"


class TestOutputSchema:
    """Validate that output conforms to the B4IU v0.1 JSON schema."""

    def test_schema_fields_present(self):
        """All required schema fields are present in output."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500)
        required_keys = {
            "b4iu_id", "tx_bit", "rx_bit", "rt_ms", "t_max_ms",
            "panic", "delta", "P", "C", "verdict",
        }
        assert required_keys == set(result.keys())

    def test_b4iu_id_value(self):
        """b4iu_id matches the spec constant."""
        result = verify_trial(tx_bit=0, rx_bit=0, rt_ms=100, t_max_ms=1000)
        assert result["b4iu_id"] == B4IU_ID

    def test_json_output_matches_dict(self):
        """verify_trial_json produces JSON that round-trips to the same dict."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500)
        json_str = verify_trial_json(tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500)
        assert json.loads(json_str) == result

    def test_spec_example(self):
        """The exact example from the B4IU v0.1 specification must pass."""
        result = verify_trial(tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500, panic=0)
        assert result == {
            "b4iu_id": "human-substrate/gad-fly/v0.1",
            "tx_bit": 1,
            "rx_bit": 1,
            "rt_ms": 412,
            "t_max_ms": 1500,
            "panic": 0,
            "delta": 1,
            "P": 0,
            "C": 1,
            "verdict": "PASS",
        }
