from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _write(tmp_path: Path, name: str, payload: object) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path

def test_verifier_cli_pass(tmp_path: Path) -> None:
    payload = {"repo": "chrislamberthome-wq/REPEAT-"}
    payload_path = _write(tmp_path, "valid.json", payload)

    proc = subprocess.run(
        [sys.executable, "-m", "verifier", str(payload_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert proc.stdout.strip() == "PASS"

def test_verifier_cli_fail(tmp_path: Path) -> None:
    payload = {"repo": "example/incorrect-repo"}
    payload_path = _write(tmp_path, "invalid.json", payload)

    proc = subprocess.run(
        [sys.executable, "-m", "verifier", str(payload_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    assert lines[0] == "FAIL"

def test_verifier_cli_usage_error() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "verifier"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 2
    assert "usage:" in proc.stderr

def test_verifier_cli_payload_load_error(tmp_path: Path) -> None:
    payload_path = tmp_path / "broken.json"
    payload_path.write_text("{not-json", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, "-m", "verifier", str(payload_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 2
    assert "ERROR payload load failed:" in proc.stderr
