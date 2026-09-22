#!/usr/bin/env python3
"""Fail-closed verification of a self-contained preservation bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SHA1 = re.compile(r"^[0-9a-f]{40}$")

# These names are the complete archive scope.  The manifest and checksum list
# are established independently and therefore are not hashes of themselves.
REQUIRED_SCOPE = {
    "preservation-manifest.json",
    "sha256sums.txt",
    "provenance.jsonl",
    "timeline.json",
}
MANIFEST_CONTROLLED = {"provenance.jsonl", "timeline.json"}


class VerificationFailure(Exception):
    pass


def fail(reason: str) -> None:
    raise VerificationFailure(reason)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"MALFORMED_METADATA: {path}: {exc}")


def digest(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"MISSING_ARTIFACT: {path}: {exc}")
    return hashlib.sha256(data).hexdigest()


def archive_path(root: Path, name: str) -> Path:
    """Resolve an archive-relative name without permitting scope escape."""
    candidate = (root / "archive" / name).resolve()
    archive = (root / "archive").resolve()
    try:
        candidate.relative_to(archive)
    except ValueError:
        fail("INVALID_ARTIFACT_PATH")
    return candidate


def verify(root: Path) -> dict[str, int | str]:
    archive = root / "archive"
    if not archive.is_dir():
        fail("MISSING_ARCHIVE_SCOPE")

    actual = {p.relative_to(archive).as_posix() for p in archive.rglob("*") if p.is_file()}
    if actual != REQUIRED_SCOPE:
        missing = sorted(REQUIRED_SCOPE - actual)
        extra = sorted(actual - REQUIRED_SCOPE)
        if missing:
            fail(f"MISSING_ARTIFACT: {missing[0]}")
        fail(f"UNEXPECTED_ARTIFACT: {extra[0]}")

    manifest_path = archive / "preservation-manifest.json"
    manifest = load_json(manifest_path)
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
    if not isinstance(artifacts, list):
        fail("INVALID_MANIFEST_ARTIFACTS")
    declared: dict[str, str] = {}
    for item in artifacts:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not SHA256.fullmatch(item.get("sha256", "")):
            fail("INVALID_MANIFEST_ARTIFACT")
        raw_path = item["path"]
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("archive",) or len(path.parts) != 2:
            fail("INVALID_ARTIFACT_PATH")
        name = path.parts[1]
        if name in declared:
            fail("DUPLICATE_ARTIFACT_DECLARATION")
        if name not in MANIFEST_CONTROLLED:
            fail("INVALID_MANIFEST_ARTIFACT")
        declared[name] = item["sha256"]
        if not archive_path(root, name).is_file():
            fail(f"MISSING_ARTIFACT: {name}")
        if digest(archive_path(root, name)) != item["sha256"]:
            fail(f"HASH_MISMATCH: {name}")
    if set(declared) != MANIFEST_CONTROLLED:
        fail("REQUIRED_ARTIFACT_OMITTED_FROM_MANIFEST")

    sums: dict[str, str] = {}
    try:
        lines = (archive / "sha256sums.txt").read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        fail(f"MALFORMED_METADATA: sha256sums.txt: {exc}")
    for line in lines:
        fields = line.split()
        if len(fields) != 2 or not SHA256.fullmatch(fields[0]):
            fail("INVALID_HASH_LIST")
        raw_path = fields[1]
        path = Path(raw_path)
        if path.is_absolute() or ".." in path.parts or path.parts[:1] != ("archive",) or len(path.parts) != 2:
            fail("INVALID_ARTIFACT_PATH")
        name = path.parts[1]
        if name in sums:
            fail("DUPLICATE_ARTIFACT_DECLARATION")
        if name not in MANIFEST_CONTROLLED:
            fail("INVALID_HASH_LIST")
        sums[name] = fields[0]
    if sums != declared:
        fail("HASH_LIST_MISMATCH")
    for name, expected in sums.items():
        if digest(archive_path(root, name)) != expected:
            fail(f"HASH_MISMATCH: {name}")

    references = 0
    try:
        for number, line in enumerate((archive / "provenance.jsonl").read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                fail(f"BROKEN_PROVENANCE_REFERENCE: line {number}")
            for key in ("source", "target"):
                if key in record:
                    target = record[key]
                    if not isinstance(target, str) or not target.startswith("archive/") or target[8:] not in declared:
                        fail(f"BROKEN_PROVENANCE_REFERENCE: line {number}")
                    references += 1
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"MALFORMED_PROVENANCE: {exc}")

    timeline = load_json(archive / "timeline.json")
    if not isinstance(timeline, list):
        fail("MALFORMED_CHRONOLOGY")
    timestamps = []
    for entry in timeline:
        if not isinstance(entry, dict) or not isinstance(entry.get("timestamp"), str):
            fail("MALFORMED_CHRONOLOGY")
        try:
            timestamps.append(datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00")))
        except ValueError:
            fail("MALFORMED_CHRONOLOGY")
    if timestamps != sorted(timestamps):
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
