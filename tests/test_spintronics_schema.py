import json
from pathlib import Path

from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "repeat-spintronics-receipt-v1.schema.json"


def test_generated_receipts_validate_against_draft7_schema() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)
    assert validator.is_valid({
        "schema": "repeat-spintronics-receipt-v1",
        "packet_hash_sha256": "sha256:" + "0" * 64,
        "evidence_hash_sha256": "sha256:" + "1" * 64,
        "receipt_hash_sha256": "sha256:" + "2" * 64,
        "run_id": 1,
        "measured_resistance_ohms": 1000,
        "verdict": {"pass": True},
        "metrics": {"mean_resistance_ohms": 1000, "drift_pct": 0}
    })
