from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"
SPINTRONICS_SCHEMA_PATH = ROOT / "schemas" / "repeat-spintronics-receipt-v1.schema.json"


def _validator(path: Path) -> Draft7Validator:
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def test_repo_reference_schema_uses_draft7_validator() -> None:
    assert isinstance(_validator(SCHEMA_PATH), Draft7Validator)


def test_spintronics_receipt_schema_uses_draft7_validator() -> None:
    assert isinstance(_validator(SPINTRONICS_SCHEMA_PATH), Draft7Validator)
