"""Scope and fail-closed tests for the preservation verifier."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.validate_preservation import VerificationFailure, verify


def make_bundle(tmp_path: Path, *, extra=None):
    archive = tmp_path / "archive"
    archive.mkdir()
    provenance = '{"source":"archive/provenance.jsonl","target":"archive/timeline.json"}\n'
    timeline = '[{"timestamp":"2026-01-01T00:00:00Z"}]\n'
    (archive / "provenance.jsonl").write_text(provenance)
    (archive / "timeline.json").write_text(timeline)
    manifest = {
        "repository": "example/repo", "commit": "a" * 40,
        "manifest_version": "0.1", "historical_claim": {"record_id": "r"},
        "technical_verification": {"status": "UNRESOLVED", "receipt_id": "x"},
        "verification": {"chat_dependency": "NONE"},
        "artifacts": [],
    }
    for name in ("provenance.jsonl", "timeline.json"):
        manifest["artifacts"].append({"path": f"archive/{name}", "sha256": hashlib.sha256((archive / name).read_bytes()).hexdigest()})
    (archive / "preservation-manifest.json").write_text(json.dumps(manifest))
    sums = "".join(f"{item['sha256']}  archive/{item['path'].split('/')[-1]}\n" for item in manifest["artifacts"])
    (archive / "sha256sums.txt").write_text(sums)
    if extra:
        for name, content in extra.items():
            (archive / name).write_text(content)
    return tmp_path


def expect_failure(bundle, text):
    with pytest.raises(VerificationFailure, match=text):
        verify(bundle)


def test_valid_structure_but_checksum_fixture_is_invalid(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "archive/sha256sums.txt").write_text("0" * 64 + "  archive/provenance.jsonl\n" + "0" * 64 + "  archive/timeline.json\n")
    expect_failure(bundle, "HASH_MISMATCH")


def test_omitted_required_artifact(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "archive/timeline.json").unlink()
    expect_failure(bundle, "MISSING_ARTIFACT")


def test_undeclared_extra_artifact(tmp_path):
    expect_failure(make_bundle(tmp_path, extra={"extra.txt": "x"}), "UNEXPECTED_ARTIFACT")


def test_altered_provenance_is_rejected(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "archive/provenance.jsonl").write_text('{"source":"archive/missing.json"}\n')
    expect_failure(bundle, "HASH_MISMATCH")


def test_altered_timeline_is_rejected(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "archive/timeline.json").write_text('[{"timestamp":"2027-01-01T00:00:00Z"}]\n')
    expect_failure(bundle, "HASH_MISMATCH")


def test_malformed_manifest(tmp_path):
    bundle = make_bundle(tmp_path)
    (bundle / "archive/preservation-manifest.json").write_text("{")
    expect_failure(bundle, "MALFORMED_METADATA")


def test_invalid_path(tmp_path):
    bundle = make_bundle(tmp_path)
    manifest = json.loads((bundle / "archive/preservation-manifest.json").read_text())
    manifest["artifacts"][0]["path"] = "archive/../timeline.json"
    (bundle / "archive/preservation-manifest.json").write_text(json.dumps(manifest))
    expect_failure(bundle, "INVALID_ARTIFACT_PATH")


def test_broken_provenance_reference(tmp_path):
    bundle = make_bundle(tmp_path)
    p = bundle / "archive/provenance.jsonl"
    p.write_text('{"source":"archive/unknown.json"}\n')
    data = json.loads((bundle / "archive/preservation-manifest.json").read_text())
    data["artifacts"][0]["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    (bundle / "archive/preservation-manifest.json").write_text(json.dumps(data))
    (bundle / "archive/sha256sums.txt").write_text(data["artifacts"][0]["sha256"] + "  archive/provenance.jsonl\n" + data["artifacts"][1]["sha256"] + "  archive/timeline.json\n")
    expect_failure(bundle, "BROKEN_PROVENANCE_REFERENCE")


def test_invalid_chronology(tmp_path):
    bundle = make_bundle(tmp_path)
    p = bundle / "archive/timeline.json"
    p.write_text('[{"timestamp":"2027-01-01T00:00:00Z"},{"timestamp":"2026-01-01T00:00:00Z"}]\n')
    expect_failure(bundle, "HASH_MISMATCH")


def test_conversational_dependency(tmp_path):
    bundle = make_bundle(tmp_path)
    path = bundle / "archive/preservation-manifest.json"
    data = json.loads(path.read_text())
    data["verification"]["chat_dependency"] = "REQUIRED"
    path.write_text(json.dumps(data))
    expect_failure(bundle, "EXTERNAL_CONVERSATIONAL_DEPENDENCY")


def test_checksum_mismatch(tmp_path):
    bundle = make_bundle(tmp_path)
    sums = bundle / "archive/sha256sums.txt"
    sums.write_text("f" * 64 + "  archive/provenance.jsonl\n" + sums.read_text().splitlines()[1] + "\n")
    expect_failure(bundle, "HASH_LIST_MISMATCH")
