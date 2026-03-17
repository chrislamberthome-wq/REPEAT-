"""Tests for governance verdict enforcement.

Guarantees under test
---------------------
- ALLOW verdict passes.
- DENY verdict halts (raises ValueError, never returns PASS).
- Unknown verdict is rejected.
- Governance record must conform to governance.schema.json.
- Missing required fields are rejected by schema validation.
"""
import copy
import json
from pathlib import Path

import pytest
import jsonschema

from delta_repeat_proof_v1.verifier.verify import check_governance, check_schema_conformance

_ROOT = Path(__file__).resolve().parent.parent
_GOV_PATH = _ROOT / "trace" / "governance.json"
_SCHEMA_PATH = _ROOT / "schemas" / "governance.schema.json"


def _load_governance():
    return json.loads(_GOV_PATH.read_bytes())


def _load_schema():
    return json.loads(_SCHEMA_PATH.read_bytes())


def test_allow_verdict_passes():
    gov = _load_governance()
    assert gov["verdict"] == "ALLOW"
    check_governance(gov)  # must not raise


def test_deny_verdict_halts():
    gov = copy.deepcopy(_load_governance())
    gov["verdict"] = "DENY"
    with pytest.raises(ValueError, match="DENY"):
        check_governance(gov)


def test_unknown_verdict_rejected():
    gov = copy.deepcopy(_load_governance())
    gov["verdict"] = "MAYBE"
    with pytest.raises(ValueError, match="verdict must be ALLOW or DENY"):
        check_governance(gov)


def test_governance_schema_valid():
    gov = _load_governance()
    schema = _load_schema()
    jsonschema.validate(gov, schema)  # must not raise


def test_governance_missing_verdict_fails_schema():
    gov = copy.deepcopy(_load_governance())
    del gov["verdict"]
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(gov, schema)


def test_governance_missing_constraints_fails_schema():
    gov = copy.deepcopy(_load_governance())
    del gov["constraints_applied"]
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(gov, schema)


def test_governance_empty_constraints_fails_schema():
    gov = copy.deepcopy(_load_governance())
    gov["constraints_applied"] = []
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(gov, schema)


def test_governance_additional_fields_rejected():
    gov = copy.deepcopy(_load_governance())
    gov["extra_field"] = "not_allowed"
    schema = _load_schema()
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(gov, schema)


def test_governance_verdict_in_receipt():
    receipt = json.loads((_ROOT / "receipt" / "receipt.json").read_bytes())
    assert receipt["governance_verdict"] == "ALLOW"
