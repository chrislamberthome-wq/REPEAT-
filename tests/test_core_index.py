import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "schemas" / "CORE_INDEX.v1.json"
VALIDATOR = ROOT / "tools" / "validate_core_index.py"


def run_validator(index_path: Path, root: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--index",
            str(index_path),
            "--root",
            str(root),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_fixture(tmp_path: Path) -> tuple[Path, Path]:
    fixture_root = tmp_path / "repo"
    shutil.copytree(ROOT, fixture_root, ignore=shutil.ignore_patterns(".git"))
    return fixture_root / "schemas" / "CORE_INDEX.v1.json", fixture_root


def write_index(index_path: Path, payload: dict) -> None:
    index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_active_core_index_validates() -> None:
    result = run_validator(INDEX)
    assert result.returncode == 0, result.stderr
    assert "CORE_INDEX_VALID" in result.stdout


def test_malformed_json_fails(tmp_path: Path) -> None:
    index_path, fixture_root = copy_fixture(tmp_path)
    index_path.write_text("{ malformed", encoding="utf-8")

    result = run_validator(index_path, fixture_root)

    assert result.returncode != 0
    assert "malformed JSON" in result.stderr


def test_duplicate_artifact_ids_fail(tmp_path: Path) -> None:
    index_path, fixture_root = copy_fixture(tmp_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["artifacts"].append(dict(payload["artifacts"][0]))
    write_index(index_path, payload)

    result = run_validator(index_path, fixture_root)

    assert result.returncode != 0
    assert "duplicate artifact_id" in result.stderr


def test_missing_registered_file_fails(tmp_path: Path) -> None:
    index_path, fixture_root = copy_fixture(tmp_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["artifacts"][0]["relative_path"] = "does-not-exist.txt"
    write_index(index_path, payload)

    result = run_validator(index_path, fixture_root)

    assert result.returncode != 0
    assert "registered artifact is missing" in result.stderr


def test_unresolved_precedence_reference_fails(tmp_path: Path) -> None:
    index_path, fixture_root = copy_fixture(tmp_path)
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["precedence"][0]["artifact_id"] = "NOT_REGISTERED_ID"
    write_index(index_path, payload)

    result = run_validator(index_path, fixture_root)

    assert result.returncode != 0
    assert "unregistered artifact_id" in result.stderr
