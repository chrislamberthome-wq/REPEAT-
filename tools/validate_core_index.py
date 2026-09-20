#!/usr/bin/env python3
"""Validate the REPEAT core artifact index and resolve its precedence winner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


EXPECTED_TIERS = tuple(range(1, 8))


class CoreIndexError(Exception):
    """Raised when the core index is invalid."""


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise CoreIndexError(f"{path}: file not found") from exc
    except json.JSONDecodeError as exc:
        raise CoreIndexError(
            f"{path}: malformed JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}"
        ) from exc


def validate_core_index(index_path: Path, root: Path) -> str:
    index = load_json(index_path)

    # CORE_INDEX.v1.json is a governed registry document that embeds its
    # instance data alongside its Draft 2020-12 schema keywords.  Validate
    # the schema's structure, but do not validate the document against itself:
    # that would treat $defs/$id/properties as registry instance properties.
    try:
        Draft202012Validator.check_schema(index)
    except SchemaError as exc:
        raise CoreIndexError(f"{index_path}: invalid Draft 2020-12 schema: {exc}") from exc

    artifacts = index.get("artifacts", [])
    artifact_ids = [artifact["artifact_id"] for artifact in artifacts]
    artifact_paths = [artifact["relative_path"] for artifact in artifacts]

    duplicate_ids = sorted(
        {value for value in artifact_ids if artifact_ids.count(value) > 1}
    )
    if duplicate_ids:
        raise CoreIndexError(
            "duplicate artifact_id entries: " + ", ".join(duplicate_ids)
        )

    duplicate_paths = sorted(
        {value for value in artifact_paths if artifact_paths.count(value) > 1}
    )
    if duplicate_paths:
        raise CoreIndexError(
            "duplicate relative_path entries: " + ", ".join(duplicate_paths)
        )

    registered = {artifact["artifact_id"]: artifact for artifact in artifacts}

    for artifact in artifacts:
        artifact_path = root / artifact["relative_path"]
        if not artifact_path.is_file():
            raise CoreIndexError(
                f"registered artifact is missing on disk: "
                f"{artifact['artifact_id']} -> {artifact['relative_path']}"
            )

    precedence = index.get("precedence", [])
    tiers = [entry["tier"] for entry in precedence]
    if tuple(tiers) != EXPECTED_TIERS:
        raise CoreIndexError(
            f"precedence must contain exactly tiers 1 through 7 in order; got {tiers}"
        )

    precedence_ids = [entry["artifact_id"] for entry in precedence]

    # REPEAT_CORE_v1 is the root abstract authority and does not require a path on disk.
    known_authority_ids = set(registered.keys()).union({"REPEAT_CORE_v1"})
    unknown_ids = sorted(set(precedence_ids) - known_authority_ids)
    if unknown_ids:
        raise CoreIndexError(
            "precedence references unregistered artifact_id(s): "
            + ", ".join(unknown_ids)
        )

    if len(set(precedence_ids)) != len(precedence_ids):
        raise CoreIndexError("precedence contains duplicate artifact references")

    winner = next(
        (
            entry["artifact_id"]
            for entry in precedence
            if entry["artifact_id"] in registered
            and (root / registered[entry["artifact_id"]]["relative_path"]).is_file()
        ),
        "REPEAT_CORE_v1",
    )

    return winner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate CORE_INDEX.v1.json and resolve its precedence winner."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path("schemas/CORE_INDEX.v1.json"),
        help="path to the core index JSON file",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repository root; defaults to the index file's grandparent",
    )
    args = parser.parse_args(argv)

    index_path = args.index.resolve()
    root = (args.root or index_path.parent.parent).resolve()

    try:
        winner = validate_core_index(index_path, root)
    except CoreIndexError as exc:
        print(f"CORE_INDEX_INVALID: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"CORE_INDEX_ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"CORE_INDEX_VALID: precedence winner is {winner}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
