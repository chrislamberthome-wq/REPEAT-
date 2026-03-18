from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "pvc"
EVID = ART / "evidence"

def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def crc16_ccitt_false(data: bytes) -> str:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def canonical_json(obj: dict) -> bytes:
    body = dict(obj)
    body.pop("timestamp_utc", None)
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")

def run_git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()

def deterministic_zip_dir(src_dir: pathlib.Path, out_zip: pathlib.Path) -> None:
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(src_dir).as_posix()
            info = zipfile.ZipInfo(rel)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())

def find_python_entry() -> str:
    return sys.executable or "python"

def main() -> int:
    shutil.rmtree(ART, ignore_errors=True)
    EVID.mkdir(parents=True, exist_ok=True)

    commit_sha = run_git("rev-parse", "HEAD")
    branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    status = run_git("status", "--short")
    repo_name = "chrislamberthome-wq/REPEAT-"

    claim = {
        "repo": repo_name,
        "branch": branch,
        "commit_sha": commit_sha,
        "claim": (
            "Given repository state X and deterministic runner Y, "
            "simulation output Z was produced and replay-verifies under REPEAT."
        ),
    }

    (EVID / "claim.json").write_text(
        json.dumps(claim, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (EVID / "git_commit.txt").write_text(commit_sha + "\n", encoding="utf-8")
    (EVID / "git_branch.txt").write_text(branch + "\n", encoding="utf-8")
    (EVID / "git_status.txt").write_text(status + "\n", encoding="utf-8")

    cmd = [find_python_entry(), "simulate_mram_runs.py"]
    run = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    (EVID / "runner_command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    (EVID / "stdout.txt").write_text(run.stdout, encoding="utf-8")
    (EVID / "stderr.txt").write_text(run.stderr, encoding="utf-8")
    (EVID / "exit_code.txt").write_text(str(run.returncode) + "\n", encoding="utf-8")

    evidence_zip = ART / "evidence.zip"
    deterministic_zip_dir(EVID, evidence_zip)

    pvc = {
        "artifact": "REPEAT_PVC_v1",
        "repo": repo_name,
        "branch": branch,
        "git_commit": commit_sha,
        "claim_hash": sha256_text(
            json.dumps(claim, sort_keys=True, separators=(",", ":"))