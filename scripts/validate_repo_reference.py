#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: missing dependency: jsonschema", file=sys.stderr)
    sys.exit(2)

def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: python scripts/validate_repo_reference.py <schema.json> <instance.json>",
            file=sys.stderr,
        )
        return 2

    schema_path = Path(sys.argv[1])
    instance_path = Path(sys.argv[2])

    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        instance = json.loads(instance_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: failed to read input: {exc}", file=sys.stderr)
        return 2

    try:
        validator_cls = jsonschema.validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
    except Exception as exc:
        print(f"ERROR: invalid schema: {exc}", file=sys.stderr)
        return 2

    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
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