from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, exceptions

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"

def test_schema_is_valid() -> None:
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except exceptions.SchemaError as exc:
        pytest.fail(f"Schema validation failed: {exc}")
