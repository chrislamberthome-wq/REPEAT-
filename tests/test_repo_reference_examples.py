from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"


def _validator() -> Draft7Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, format_checker=Draft7Validator.FORMAT_CHECKER)


def test_minimal_valid_repo_reference() -> None:
    payload = {"repo": "chrislamberthome-wq/REPEAT-"}
    errors = sorted(_validator().iter_errors(payload), key=lambda e: e.path)
    assert errors == []


def test_invalid_repo_reference_rejected() -> None:
    payload = {"repo": "not-the-allowed-repo"}
    errors = sorted(_validator().iter_errors(payload), key=lambda e: e.path)
    assert errors, "expected schema validation errors for invalid payload"
    messages = [e.message for e in errors]
    assert any("does not match" in message or "is not" in message for message in messages)


def test_missing_repo_field_rejected() -> None:
    errors = sorted(_validator().iter_errors({}), key=lambda e: e.path)
    assert errors, "expected schema validation errors for missing repo field"
    assert any("'repo' is a required property" in e.message for e in errors)
