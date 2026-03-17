#!/usr/bin/env python3
"""
Verification matrix harness for delta_repeat_proof_v1.

Performs three operations in sequence:
  1. Baseline verification   — must exit 0, receipt PASS
  2. Determinism runs        — N repeated runs must produce identical receipt SHA-256
  3. Adversarial mutations   — all four tamper classes must exit non-zero and produce FAIL

Output: JSON with one record per check.

Usage (from repo root):
    python delta_repeat_proof_v1/scripts/run_verification_matrix.py
    python delta_repeat_proof_v1/scripts/run_verification_matrix.py > certification/verification_matrix.json

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPTS_DIR = Path(__file__).parent
ARTIFACT_ROOT = _SCRIPTS_DIR.parent    # delta_repeat_proof_v1/
DETERMINISM_RUNS = 5


# ---------------------------------------------------------------------------
# Internal helpers (duplicated from test_adversarial to keep harness self-contained)
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _copy_artifact(tmp_dir: str) -> Path:
    dst = Path(tmp_dir) / "artifact"
    shutil.copytree(str(ARTIFACT_ROOT), str(dst))
    receipt = dst / "receipt" / "receipt.json"
    if receipt.exists():
        receipt.unlink()
    return dst


def _run_verifier(artifact_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "verifier/verify.py"],
        cwd=str(artifact_dir),
        capture_output=True,
        text=True,
    )


def _read_receipt(artifact_dir: Path) -> Optional[Dict[str, Any]]:
    receipt_path = artifact_dir / "receipt" / "receipt.json"
    if not receipt_path.exists():
        return None
    with open(receipt_path) as f:
        return json.loads(f.read())


def _file_sha256(path: Path) -> str:
    return _sha256hex(path.read_bytes())


def _read_trace_lines(artifact_dir: Path) -> List[str]:
    with open(artifact_dir / "trace.jsonl") as f:
        return f.readlines()


def _write_trace_lines(artifact_dir: Path, lines: List[str]) -> None:
    with open(artifact_dir / "trace.jsonl", "w") as f:
        f.writelines(lines)


# ---------------------------------------------------------------------------
# Check runners
# ---------------------------------------------------------------------------

def check_baseline() -> Dict[str, Any]:
    """Run the verifier once against the original artifact."""
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)
        result = _run_verifier(artifact)
        receipt = _read_receipt(artifact)
        receipt_sha256 = (
            _file_sha256(artifact / "receipt" / "receipt.json")
            if receipt is not None
            else None
        )
        status = receipt.get("status") if receipt else None
        passed = result.returncode == 0 and status == "PASS"
        return {
            "check": "baseline",
            "exit_code": result.returncode,
            "receipt_status": status,
            "receipt_sha256": receipt_sha256,
            "passed": passed,
        }


def check_determinism() -> Dict[str, Any]:
    """Run the verifier DETERMINISM_RUNS times and compare receipt hashes."""
    hashes: List[str] = []
    exit_codes: List[int] = []
    with tempfile.TemporaryDirectory() as tmp:
        # Use a single artifact directory for all runs (receipt is overwritten)
        artifact = _copy_artifact(tmp)
        for _ in range(DETERMINISM_RUNS):
            result = _run_verifier(artifact)
            exit_codes.append(result.returncode)
            receipt_path = artifact / "receipt" / "receipt.json"
            if receipt_path.exists():
                hashes.append(_file_sha256(receipt_path))
            else:
                hashes.append("MISSING")

    consistent = len(set(hashes)) == 1 and "MISSING" not in hashes
    all_pass = all(c == 0 for c in exit_codes)
    return {
        "check": "determinism",
        "runs": DETERMINISM_RUNS,
        "receipt_sha256": hashes[0] if hashes else None,
        "all_receipts_identical": consistent,
        "all_exit_codes_zero": all_pass,
        "passed": consistent and all_pass,
    }


def _adversarial_hash_break() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)
        lines = _read_trace_lines(artifact)
        step = json.loads(lines[0])
        step["verdict"] = "CORRUPTED"
        lines[0] = _canonical_json(step).decode("utf-8") + "\n"
        _write_trace_lines(artifact, lines)
        result = _run_verifier(artifact)
        receipt = _read_receipt(artifact)
        status = receipt.get("status") if receipt else None
        return {
            "mutant": "hash_chain_break",
            "exit_code": result.returncode,
            "receipt_status": status,
            "passed": result.returncode == 1 and status == "FAIL",
        }


def _adversarial_canonical_break() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)
        lines = _read_trace_lines(artifact)
        step = json.loads(lines[0])
        lines[0] = json.dumps(step, sort_keys=True, indent=2) + "\n"
        _write_trace_lines(artifact, lines)
        result = _run_verifier(artifact)
        receipt = _read_receipt(artifact)
        status = receipt.get("status") if receipt else None
        passed = result.returncode in (1, 2) and status != "PASS"
        return {
            "mutant": "non_canonical_json",
            "exit_code": result.returncode,
            "receipt_status": status,
            "passed": passed,
        }


def _adversarial_replay_break() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)
        task_path = artifact / "input" / "cognitive_task.json"
        with open(task_path) as f:
            task = json.load(f)
        task["expected_output"] = "WRONG_OUTPUT"
        with open(task_path, "w") as f:
            json.dump(task, f)
        result = _run_verifier(artifact)
        receipt = _read_receipt(artifact)
        status = receipt.get("status") if receipt else None
        replay_match = receipt.get("replay_match") if receipt else None
        return {
            "mutant": "replay_mismatch",
            "exit_code": result.returncode,
            "receipt_status": status,
            "replay_match": replay_match,
            "passed": result.returncode == 1 and status == "FAIL" and replay_match is False,
        }


def _adversarial_governance_deny() -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)
        lines = _read_trace_lines(artifact)
        new_lines: List[str] = []
        prev_hash = "0" * 64
        for raw_line in lines:
            step = json.loads(raw_line.strip())
            if step.get("action") == "governance_check":
                step["verdict"] = "DENY"
            step["prev_hash"] = prev_hash
            step_without_hash = {k: v for k, v in step.items() if k != "hash"}
            step["hash"] = _sha256hex(_canonical_json(step_without_hash))
            prev_hash = step["hash"]
            new_lines.append(_canonical_json(step).decode("utf-8") + "\n")
        _write_trace_lines(artifact, new_lines)
        result = _run_verifier(artifact)
        receipt = _read_receipt(artifact)
        status = receipt.get("status") if receipt else None
        gov = receipt.get("governance_verdict") if receipt else None
        return {
            "mutant": "governance_deny",
            "exit_code": result.returncode,
            "receipt_status": status,
            "governance_verdict": gov,
            "passed": result.returncode == 1 and status == "FAIL",
        }


def check_adversarial() -> Dict[str, Any]:
    results = [
        _adversarial_hash_break(),
        _adversarial_canonical_break(),
        _adversarial_replay_break(),
        _adversarial_governance_deny(),
    ]
    all_passed = all(r["passed"] for r in results)
    return {
        "check": "adversarial",
        "mutants": results,
        "passed": all_passed,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    matrix = {
        "artifact": "delta_repeat_proof_v1",
        "checks": [],
    }

    baseline = check_baseline()
    matrix["checks"].append(baseline)

    determinism = check_determinism()
    matrix["checks"].append(determinism)

    adversarial = check_adversarial()
    matrix["checks"].append(adversarial)

    all_passed = all(c["passed"] for c in matrix["checks"])
    matrix["overall_passed"] = all_passed

    print(json.dumps(matrix, indent=2))

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
