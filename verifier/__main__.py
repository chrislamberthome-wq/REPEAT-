from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "repo-reference.schema.json"

def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))

def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if len(args) != 1:
        print("usage: python -m verifier <payload.json>", file=sys.stderr)
        return 2

    payload_path = Path(args[0])

    try:
        schema = _load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except Exception as exc:
        print(f"ERROR schema load/validation failed: {exc}", file=sys.stderr)
        return 2

    try:
        payload = _load_json(payload_path)
    except Exception as exc:
        print(f"ERROR payload load failed: {payload_path}: {exc}", file=sys.stderr)
        return 2

    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))

    if errors:
        print("FAIL")
        for err in errors:
            path = ".".join(str(p) for p in err.path) or "<root>"
            print(f"{path}: {err.message}")
        return 1

    print("PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
