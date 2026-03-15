from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_repo_reference.py"
SCHEMA = ROOT / "schemas" / "repo-reference.schema.json"
VALID = ROOT / "examples" / "repo-reference.valid.json"
INVALID = ROOT / "examples" / "repo-reference.invalid.json"

def run_validator(instance: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(SCHEMA), str(instance)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

def test_valid_instance_passes() -> None:
    result = run_validator(VALID)
    assert result.returncode == 0
    assert result.stdout.strip() == "PASS"
    assert result.stderr.strip() == ""

def test_invalid_instance_fails() -> None:
    result = run_validator(INVALID)
    assert result.returncode == 1

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert lines
    assert lines[0] == "FAIL"
    assert any("repo" in line for line in lines[1:])

    assert result.stderr.strip() == ""