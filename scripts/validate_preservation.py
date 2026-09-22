#!/usr/bin/env python3
"""Fail-closed verification of a self-contained preservation bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")
REQUIRED = {"archive/preservation-manifest.json", "archive/sha256sums.txt", "archive/provenance.jsonl", "archive/timeline.json"}


class VerificationFailure(Exception):
    pass


def fail(reason: str) -> None:
    raise VerificationFailure(reason)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"INVALID_ARCHIVE: {path}: {exc}")


def digest(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"MISSING_ARTIFACT: {path}: {exc}")
    return hashlib.sha256(data).hexdigest()


def verify(root: Path) -> dict[str, int | str]:
    for relative in REQUIRED:
        if not (root / relative).is_file():
            fail(f"MISSING_ARTIFACT: {relative}")

    manifest = load_json(root / "archive/preservation-manifest.json")
    if not isinstance(manifest, dict):
        fail("INVALID_MANIFEST")
    if manifest.get("manifest_version") != "0.1":
        fail("INVALID_MANIFEST_VERSION")
    if not isinstance(manifest.get("repository"), str) or not SHA1.fullmatch(manifest.get("commit", "")):
        fail("MISSING_TECHNICAL_IDENTITY")
    historical = manifest.get("historical_claim")
    technical = manifest.get("technical_verification")
    if not isinstance(historical, dict) or not isinstance(technical, dict):
        fail("CONFLATED_HISTORICAL_TECHNICAL_FIELDS")
    if "record_id" not in historical or "status" not in technical or "receipt_id" not in technical:
        fail("CONFLATED_HISTORICAL_TECHNICAL_FIELDS")
    if technical["status"] not in {"PASS", "FAIL", "UNRESOLVED"}:
        fail("INVALID_TECHNICAL_STATUS")
    verification = manifest.get("verification")
    if not isinstance(verification, dict) or verification.get("chat_dependency") != "NONE":
        fail("EXTERNAL_CONVERSATIONAL_DEPENDENCY")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        fail("INVALID_MANIFEST_ARTIFACTS")
    declared: dict[str, str] = {}
    for item in artifacts:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not SHA256.fullmatch(item.get("sha256", "")):
            fail("INVALID_MANIFEST_ARTIFACT")
        path = item["path"]
        if path in declared or Path(path).is_absolute() or ".." in Path(path).parts:
            fail("INVALID_ARTIFACT_PATH")
        declared[path] = item["sha256"]
        if not (root / path).is_file():
            fail(f"MISSING_ARTIFACT: {path}")
        if digest(root / path) != item["sha256"]:
            fail(f"HASH_MISMATCH: {path}")

    sums: dict[str, str] = {}
    try:
        lines = (root / "archive/sha256sums.txt").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        fail(f"INVALID_HASH_LIST: {exc}")
    for line in lines:
        fields = line.split()
        if len(fields) != 2 or not SHA256.fullmatch(fields[0]):
            fail("INVALID_HASH_LIST")
        sums[fields[1]] = fields[0]
    if sums != declared:
        fail("HASH_LIST_MISMATCH")
    for path, expected in sums.items():
        if digest(root / path) != expected:
            fail(f"HASH_MISMATCH: {path}")

    provenance_path = root / "archive/provenance.jsonl"
    references = 0
    try:
        for number, line in enumerate(provenance_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                fail(f"BROKEN_PROVENANCE_REFERENCE: line {number}")
            for key in ("source", "target"):
                if key in record:
                    target = record[key]
                    if not isinstance(target, str) or target not in declared:
                        fail(f"BROKEN_PROVENANCE_REFERENCE: line {number}")
                    references += 1
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"MALFORMED_PROVENANCE: {exc}")

    timeline = load_json(root / "archive/timeline.json")
    if not isinstance(timeline, list):
        fail("MALFORMED_CHRONOLOGY")
    timestamps = [entry.get("timestamp") for entry in timeline if isinstance(entry, dict) and "timestamp" in entry]
    if any(not isinstance(value, str) for value in timestamps) or timestamps != sorted(timestamps):
        fail("MALFORMED_CHRONOLOGY")

    return {"artifacts": len(declared), "hashes": len(sums), "provenance": references}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an independent preservation archive")
    parser.add_argument("archive", nargs="?", default=".", help="extracted archive root")
    args = parser.parse_args()
    try:
        counts = verify(Path(args.archive).resolve())
    except VerificationFailure as exc:
        print("PRESERVATION_TEST: FAIL_CLOSED")
        print(f"REASON: {exc}")
        return 1
    print("PRESERVATION_TEST: PASS")
    print(f"ARCHIVE: {Path(args.archive).resolve()}")
    print(f"ARTIFACTS_VERIFIED: {counts['artifacts']}")
    print(f"HASHES_VERIFIED: {counts['hashes']}")
    print(f"PROVENANCE_LINKS_VERIFIED: {counts['provenance']}")
    print("CHRONOLOGY: PASS")
    print("TECHNICAL_IDENTITY: PASS")
    print("CHAT_DEPENDENCY: NONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
