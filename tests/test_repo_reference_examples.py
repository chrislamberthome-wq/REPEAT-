from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"
VECTORS = ROOT / "tests" / "vectors" / "repo_reference"


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _load(name: str) -> dict[str, object]:
    return json.loads((VECTORS / name).read_text(encoding="utf-8"))


def test_valid_minimal_vector():
    payload = _load("valid_minimal.json")
    errors = sorted(_validator().iter_errors(payload), key=lambda e: e.path)
    assert errors == []


def test_invalid_enum_vector():
    payload = _load("invalid_enum.json")
    errors = sorted(_validator().iter_errors(payload), key=lambda e: e.path)
    assert errors, "expected schema validation errors"


def test_missing_repo_vector():
    payload = _load("missing_repo.json")
    errors = sorted(_validator().iter_errors(payload), key=lambda e: e.path)
    assert errors, "expected schema validation errors"
