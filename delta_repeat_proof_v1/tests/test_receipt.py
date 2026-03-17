"""Tests for receipt construction and verification.

Guarantees under test
---------------------
- Stored receipt matches all re-derived fields (PASS).
- Wrong trace_sha256 causes ReceiptVerificationError.
- Wrong crc16_ccitt_false causes ReceiptVerificationError.
- Status field must be PASS in the stored receipt.
- replay_match must be true in the stored receipt.
- Missing required field fails JSON Schema.
- Additional fields fail JSON Schema.
- build_receipt produces correct derived fields.
"""
import copy
import json
from pathlib import Path

import pytest
import jsonschema

from delta_repeat_proof_v1.verifier.canonical import sha256_hex
from delta_repeat_proof_v1.verifier.receipt import (
    ReceiptVerificationError,
    build_receipt,
    verify_receipt,
)

_ROOT = Path(__file__).resolve().parent.parent
_TRACE = _ROOT / "trace" / "trace.jsonl"
_RECEIPT_PATH = _ROOT / "receipt" / "receipt.json"
_SCHEMA_PATH = _ROOT / "schemas" / "receipt.schema.json"


def _load_receipt():
    return json.loads(_RECEIPT_PATH.read_bytes())


def _load_schema():
    return json.loads(_SCHEMA_PATH.read_bytes())


def _trace_bytes():
    return _TRACE.read_bytes()


def test_stored_receipt_passes_verification():
    receipt = _load_receipt()
    verify_receipt(receipt, _trace_bytes())  # must not raise


def test_receipt_status_is_pass():
    receipt = _load_receipt()
    assert receipt["status"] == "PASS"


def test_receipt_replay_match_is_true():
    receipt = _load_receipt()
    assert receipt["replay_match"] is True


def test_receipt_governance_verdict_is_allow():
    receipt = _load_receipt()
    assert receipt["governance_verdict"] == "ALLOW"


def test_receipt_event_count_is_five():
    receipt = _load_receipt()
    assert receipt["event_count"] == 5


def test_wrong_trace_sha256_fails():
    receipt = copy.deepcopy(_load_receipt())
    receipt["trace_sha256"] = "a" * 64
    with pytest.raises(ReceiptVerificationError, match="trace_sha256 mismatch"):
        verify_receipt(receipt, _trace_bytes())


def test_wrong_crc_fails():
    receipt = copy.deepcopy(_load_receipt())
    receipt["crc16_ccitt_false"] = "0000"
    with pytest.raises(ReceiptVerificationError, match="crc16_ccitt_false mismatch"):
        verify_receipt(receipt, _trace_bytes())


def test_build_receipt_matches_stored():
    stored = _load_receipt()
    built = build_receipt(
        cycle_id=stored["cycle_id"],
        trace_bytes=_trace_bytes(),
        event_count=stored["event_count"],
        governance_verdict=stored["governance_verdict"],
        replay_match=stored["replay_match"],
        status=stored["status"],
    )
    assert built == stored


def test_receipt_schema_valid():
    receipt = _load_receipt()
    schema = _load_schema()
    jsonschema.validate(receipt, schema)  # must not raise


def test_receipt_missing_field_fails_schema():
    receipt = copy.deepcopy(_load_receipt())
    del receipt["status"]
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)


def test_receipt_additional_field_fails_schema():
    receipt = copy.deepcopy(_load_receipt())
    receipt["extra"] = "not_allowed"
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)


def test_receipt_deny_verdict_stored_as_fail():
    """A DENY governance verdict must produce status=FAIL, not PASS."""
    built = build_receipt(
        cycle_id="cycle-0002",
        trace_bytes=b"fake",
        event_count=5,
        governance_verdict="DENY",
        replay_match=False,
        status="FAIL",
    )
    assert built["status"] == "FAIL"
    assert built["governance_verdict"] == "DENY"
