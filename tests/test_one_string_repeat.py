"""
Tests for one_string_REPEAT v1.0 modules.

Covers:
- canonical.py: JCS serialisation, duplicate-key rejection, NaN/Infinity rejection
- crc16.py: CRC-16/CCITT-FALSE correctness
- hashutil.py: SHA-256 correctness
- engine.py: fixed_point rule, error cases
- receipt.py: run_receipt generation, hash/crc binding
- replay.py: deterministic replay, byte-stability
- verifier.py: verification_receipt, PASS/FAIL/ERROR truth states
- verify_run.py (certify()): end-to-end loop
"""
from __future__ import annotations

import json

import pytest

from one_string_repeat.canonical import canonicalize, canonicalize_string
from one_string_repeat.crc16 import crc16_ccitt_false, crc16_hex
from one_string_repeat.engine import execute
from one_string_repeat.hashutil import sha256_hex
from one_string_repeat.receipt import generate as generate_receipt
from one_string_repeat.replay import replay_from_bytes, replay_from_payload
from one_string_repeat.verifier import verify
from one_string_repeat.verify_run import certify

# ---------------------------------------------------------------------------
# canonical.py
# ---------------------------------------------------------------------------


class TestCanonical:
    def test_key_sort(self):
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonicalize(obj).decode("utf-8")
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        obj = {"x": 1}
        result = canonicalize(obj).decode("utf-8")
        assert " " not in result

    def test_utf8_encoding(self):
        obj = {"key": "héllo"}
        raw = canonicalize(obj)
        assert isinstance(raw, bytes)
        decoded = raw.decode("utf-8")
        assert "héllo" in decoded

    def test_nan_rejected(self):
        import math

        obj = {"v": math.nan}
        with pytest.raises(ValueError):
            canonicalize(obj)

    def test_inf_rejected(self):
        import math

        obj = {"v": math.inf}
        with pytest.raises(ValueError):
            canonicalize(obj)

    def test_duplicate_keys_rejected(self):
        raw = '{"a": 1, "a": 2}'
        with pytest.raises(ValueError, match="Duplicate key"):
            canonicalize_string(raw)

    def test_non_dict_rejected(self):
        with pytest.raises(TypeError):
            canonicalize([1, 2, 3])  # type: ignore[arg-type]

    def test_canonicalize_string_array_rejected(self):
        with pytest.raises(ValueError, match="JSON object"):
            canonicalize_string("[1, 2, 3]")

    def test_nested_key_sort(self):
        obj = {"b": {"z": 1, "a": 2}, "a": 0}
        result = json.loads(canonicalize(obj))
        # Canonical bytes should be parseable and equal to the original value
        assert result == obj

    def test_identical_input_same_bytes(self):
        obj = {"rule": "fixed_point", "initial_value": 8, "max_steps": 4}
        assert canonicalize(obj) == canonicalize(obj)

    def test_invalid_json_string(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            canonicalize_string("{not valid json}")


# ---------------------------------------------------------------------------
# crc16.py
# ---------------------------------------------------------------------------


class TestCrc16:
    def test_known_value(self):
        # CRC-16/CCITT-FALSE of b"123456789" is 0x29B1
        assert crc16_ccitt_false(b"123456789") == 0x29B1

    def test_empty_bytes(self):
        assert crc16_ccitt_false(b"") == 0xFFFF

    def test_hex_format(self):
        result = crc16_hex(b"123456789")
        assert result == "29B1"
        assert len(result) == 4
        assert result == result.upper()

    def test_non_bytes_rejected(self):
        with pytest.raises(TypeError):
            crc16_ccitt_false("hello")  # type: ignore[arg-type]

    def test_deterministic(self):
        data = b"one_string_REPEAT"
        assert crc16_ccitt_false(data) == crc16_ccitt_false(data)


# ---------------------------------------------------------------------------
# hashutil.py
# ---------------------------------------------------------------------------


class TestHashutil:
    def test_sha256_known(self):
        # SHA-256 of b"" is well-known
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert sha256_hex(b"") == expected

    def test_sha256_length(self):
        assert len(sha256_hex(b"hello")) == 64

    def test_sha256_lowercase(self):
        result = sha256_hex(b"test")
        assert result == result.lower()

    def test_non_bytes_rejected(self):
        with pytest.raises(TypeError):
            sha256_hex("hello")  # type: ignore[arg-type]

    def test_deterministic(self):
        data = b"one_string"
        assert sha256_hex(data) == sha256_hex(data)


# ---------------------------------------------------------------------------
# engine.py
# ---------------------------------------------------------------------------

VALID_INPUT = {"rule": "fixed_point", "initial_value": 8, "max_steps": 4}


class TestEngine:
    def test_fixed_point_pass(self):
        result, exit_code, output, errors = execute(VALID_INPUT)
        assert result == "PASS"
        assert exit_code == 0
        assert output["final_value"] == 8
        assert output["steps_executed"] == 1
        assert output["fixed_point_reached"] is True
        assert errors == []

    def test_fixed_point_deterministic(self):
        r1 = execute(VALID_INPUT)
        r2 = execute(VALID_INPUT)
        assert r1 == r2

    def test_unknown_rule(self):
        result, exit_code, output, errors = execute({"rule": "unknown_rule"})
        assert result == "ERROR"
        assert exit_code == 2
        assert output == {}
        assert errors

    def test_missing_rule(self):
        result, exit_code, output, errors = execute({"initial_value": 1, "max_steps": 1})
        assert result == "ERROR"
        assert exit_code == 2

    def test_missing_initial_value(self):
        result, exit_code, output, errors = execute({"rule": "fixed_point", "max_steps": 4})
        assert result == "ERROR"
        assert exit_code == 2

    def test_missing_max_steps(self):
        result, exit_code, output, errors = execute({"rule": "fixed_point", "initial_value": 8})
        assert result == "ERROR"
        assert exit_code == 2

    def test_invalid_max_steps(self):
        result, exit_code, output, errors = execute(
            {"rule": "fixed_point", "initial_value": 8, "max_steps": 0}
        )
        assert result == "ERROR"
        assert exit_code == 2

    def test_non_dict_input(self):
        result, exit_code, output, errors = execute("not a dict")  # type: ignore[arg-type]
        assert result == "ERROR"
        assert exit_code == 2

    def test_different_initial_values(self):
        for val in [0, 1, 100, -5]:
            result, exit_code, output, errors = execute(
                {"rule": "fixed_point", "initial_value": val, "max_steps": 10}
            )
            assert result == "PASS"
            assert output["final_value"] == val


# ---------------------------------------------------------------------------
# receipt.py
# ---------------------------------------------------------------------------

VALID_PAYLOAD: dict = {
    "schema_version": "1.0.0",
    "payload_type": "one_string_run",
    "engine_name": "one_string_repeat",
    "engine_version": "1.0.0",
    "canonicalization": "JCS",
    "input_schema": "run_config.schema.json",
    "input": {
        "rule": "fixed_point",
        "initial_value": 8,
        "max_steps": 4,
    },
}


class TestReceipt:
    def test_generates_pass_receipt(self):
        receipt = generate_receipt(VALID_PAYLOAD)
        assert receipt["result"] == "PASS"
        assert receipt["exit_code"] == 0
        assert receipt["errors"] == []

    def test_receipt_has_correct_shape(self):
        receipt = generate_receipt(VALID_PAYLOAD)
        required = {
            "schema_version", "receipt_type", "engine_name", "engine_version",
            "payload_sha256", "payload_crc16_ccitt_false", "executed_at",
            "result", "exit_code", "output", "trace_sha256", "errors",
        }
        assert required <= receipt.keys()

    def test_sha256_matches_canonical_payload(self):
        receipt = generate_receipt(VALID_PAYLOAD)
        payload_bytes = canonicalize(VALID_PAYLOAD)
        assert receipt["payload_sha256"] == sha256_hex(payload_bytes)

    def test_crc16_matches_canonical_payload(self):
        receipt = generate_receipt(VALID_PAYLOAD)
        payload_bytes = canonicalize(VALID_PAYLOAD)
        assert receipt["payload_crc16_ccitt_false"] == crc16_hex(payload_bytes)

    def test_output_matches_engine(self):
        receipt = generate_receipt(VALID_PAYLOAD)
        _, _, expected_output, _ = execute(VALID_PAYLOAD["input"])
        assert receipt["output"] == expected_output

    def test_deterministic(self):
        r1 = generate_receipt(VALID_PAYLOAD)
        r2 = generate_receipt(VALID_PAYLOAD)
        # All fields except executed_at (timestamp) must be identical
        for key in r1:
            if key != "executed_at":
                assert r1[key] == r2[key], f"mismatch in field {key!r}"

    def test_missing_payload_field_gives_error(self):
        bad_payload = dict(VALID_PAYLOAD)
        del bad_payload["input"]
        receipt = generate_receipt(bad_payload)
        assert receipt["result"] == "ERROR"
        assert receipt["exit_code"] == 2
        assert receipt["errors"]

    def test_wrong_engine_name_gives_error(self):
        bad = dict(VALID_PAYLOAD, engine_name="other_engine")
        receipt = generate_receipt(bad)
        assert receipt["result"] == "ERROR"

    def test_non_dict_payload_gives_error(self):
        receipt = generate_receipt("not a dict")  # type: ignore[arg-type]
        assert receipt["result"] == "ERROR"


# ---------------------------------------------------------------------------
# replay.py
# ---------------------------------------------------------------------------


class TestReplay:
    def test_replay_from_bytes_matches_execute(self):
        payload_bytes = canonicalize(VALID_PAYLOAD)
        r, ec, out, errs = replay_from_bytes(payload_bytes)
        _, _, expected_out, _ = execute(VALID_PAYLOAD["input"])
        assert r == "PASS"
        assert out == expected_out
        assert errs == []

    def test_replay_from_payload_matches_execute(self):
        r, ec, out, errs = replay_from_payload(VALID_PAYLOAD)
        _, _, expected_out, _ = execute(VALID_PAYLOAD["input"])
        assert r == "PASS"
        assert out == expected_out

    def test_invalid_bytes_gives_error(self):
        r, ec, out, errs = replay_from_bytes(b"not json")
        assert r == "ERROR"
        assert errs

    def test_non_bytes_gives_error(self):
        r, ec, out, errs = replay_from_bytes("a string")  # type: ignore[arg-type]
        assert r == "ERROR"

    def test_deterministic(self):
        payload_bytes = canonicalize(VALID_PAYLOAD)
        r1 = replay_from_bytes(payload_bytes)
        r2 = replay_from_bytes(payload_bytes)
        assert r1 == r2


# ---------------------------------------------------------------------------
# verifier.py
# ---------------------------------------------------------------------------


class TestVerifier:
    def _valid_receipt(self):
        return generate_receipt(VALID_PAYLOAD)

    def test_verification_pass(self):
        receipt = self._valid_receipt()
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["verification_result"] == "PASS"
        assert vr["verification_exit_code"] == 0
        assert vr["matched_payload_hash"] is True
        assert vr["matched_payload_crc16"] is True
        assert vr["matched_output"] is True
        assert vr["matched_exit_code"] is True

    def test_tampered_sha256_gives_fail(self):
        receipt = self._valid_receipt()
        receipt["payload_sha256"] = "a" * 64
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["verification_result"] == "FAIL"
        assert vr["matched_payload_hash"] is False

    def test_tampered_crc16_gives_fail(self):
        receipt = self._valid_receipt()
        receipt["payload_crc16_ccitt_false"] = "0000"
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["verification_result"] == "FAIL"
        assert vr["matched_payload_crc16"] is False

    def test_tampered_output_gives_fail(self):
        receipt = self._valid_receipt()
        receipt["output"] = {"final_value": 999, "steps_executed": 99, "fixed_point_reached": False}
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["verification_result"] == "FAIL"
        assert vr["matched_output"] is False

    def test_tampered_exit_code_gives_fail(self):
        receipt = self._valid_receipt()
        receipt["exit_code"] = 1  # was 0
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["verification_result"] == "FAIL"
        assert vr["matched_exit_code"] is False

    def test_non_dict_payload_gives_error(self):
        receipt = self._valid_receipt()
        vr = verify("not a dict", receipt)  # type: ignore[arg-type]
        assert vr["verification_result"] == "ERROR"

    def test_non_dict_receipt_gives_error(self):
        vr = verify(VALID_PAYLOAD, "not a dict")  # type: ignore[arg-type]
        assert vr["verification_result"] == "ERROR"

    def test_missing_receipt_fields_gives_error(self):
        vr = verify(VALID_PAYLOAD, {"partial": True})
        assert vr["verification_result"] == "ERROR"

    def test_verification_receipt_shape(self):
        receipt = self._valid_receipt()
        vr = verify(VALID_PAYLOAD, receipt)
        required = {
            "schema_version", "receipt_type", "verifier_name", "verifier_version",
            "verified_at", "payload_sha256", "payload_crc16_ccitt_false",
            "claimed_result", "replayed_result",
            "matched_payload_hash", "matched_payload_crc16",
            "matched_output", "matched_exit_code",
            "verification_result", "verification_exit_code", "notes",
        }
        assert required <= vr.keys()

    def test_notes_empty_on_pass(self):
        receipt = self._valid_receipt()
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["notes"] == []

    def test_notes_non_empty_on_fail(self):
        receipt = self._valid_receipt()
        receipt["payload_sha256"] = "b" * 64
        vr = verify(VALID_PAYLOAD, receipt)
        assert vr["notes"]


# ---------------------------------------------------------------------------
# verify_run.py (certify)
# ---------------------------------------------------------------------------


class TestCertify:
    def test_certify_valid_payload(self):
        code = certify(VALID_PAYLOAD, verbose=False, as_json=False)
        assert code == 0

    def test_certify_as_json(self, capsys):
        code = certify(VALID_PAYLOAD, verbose=True, as_json=True)
        captured = capsys.readouterr()
        out = json.loads(captured.out)
        assert "run_receipt" in out
        assert "verification_receipt" in out
        assert out["verification_receipt"]["verification_result"] == "PASS"
        assert code == 0

    def test_certify_invalid_payload_gives_error(self):
        bad = {}
        code = certify(bad, verbose=False, as_json=False)
        assert code == 2

    def test_certify_different_payloads_give_different_hashes(self):
        p1 = dict(VALID_PAYLOAD, input={"rule": "fixed_point", "initial_value": 1, "max_steps": 1})
        p2 = dict(VALID_PAYLOAD, input={"rule": "fixed_point", "initial_value": 2, "max_steps": 1})
        r1 = generate_receipt(p1)
        r2 = generate_receipt(p2)
        assert r1["payload_sha256"] != r2["payload_sha256"]
