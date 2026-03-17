"""
Adversarial tests for delta_repeat_proof_v1.

Each test:
  1. Stages a temporary copy of the proof artifact
  2. Mutates exactly one surface
  3. Runs verifier/verify.py
  4. Asserts the expected exit code and receipt status

Tamper classes covered:
  A. Hash-chain break     → exit 1, status FAIL
  B. Non-canonical JSON   → exit 1, status FAIL
  C. Replay divergence    → exit 1, status FAIL
  D. Governance DENY      → exit 1, status FAIL
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
from typing import Any, Dict, Optional

# Locate the delta_repeat_proof_v1 root
_HERE = Path(__file__).parent          # delta_repeat_proof_v1/tests/
ARTIFACT_ROOT = _HERE.parent           # delta_repeat_proof_v1/


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _copy_artifact(tmp_dir: str) -> Path:
    """Copy the full artifact into a temp directory and return its path."""
    dst = Path(tmp_dir) / "artifact"
    shutil.copytree(str(ARTIFACT_ROOT), str(dst))
    # Remove any pre-existing receipt so each run starts clean
    receipt = dst / "receipt" / "receipt.json"
    if receipt.exists():
        receipt.unlink()
    return dst


def _run_verifier(artifact_dir: Path) -> subprocess.CompletedProcess:
    """Run verifier/verify.py from within artifact_dir."""
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


def _read_trace_lines(artifact_dir: Path):
    with open(artifact_dir / "trace.jsonl") as f:
        return f.readlines()


def _write_trace_lines(artifact_dir: Path, lines):
    with open(artifact_dir / "trace.jsonl", "w") as f:
        f.writelines(lines)


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


# ---------------------------------------------------------------------------
# Test A: Hash-chain break
# ---------------------------------------------------------------------------

def test_hash_chain_break():
    """
    Mutate a data field in trace step 1 without updating its hash.
    The stored hash no longer matches the computed hash.
    Expected: exit 1, receipt status FAIL.
    """
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)

        lines = _read_trace_lines(artifact)
        # Corrupt the first step: flip one character in its 'verdict' field
        step = json.loads(lines[0])
        step["verdict"] = "CORRUPTED"
        # Re-serialise in canonical form but with the OLD (now wrong) hash intact
        corrupted_line = _canonical_json(step).decode("utf-8") + "\n"
        lines[0] = corrupted_line
        _write_trace_lines(artifact, lines)

        result = _run_verifier(artifact)
        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        receipt = _read_receipt(artifact)
        assert receipt is not None, "Receipt was not written"
        assert receipt["status"] == "FAIL", (
            f"Expected receipt status FAIL, got {receipt['status']}"
        )


# ---------------------------------------------------------------------------
# Test B: Non-canonical JSON (canonicalization break)
# ---------------------------------------------------------------------------

def test_non_canonical_json():
    """
    Reformat a trace step by adding whitespace, breaking canonical form.
    Expected: exit 1, receipt status FAIL (never PASS).
    """
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)

        lines = _read_trace_lines(artifact)
        # Reformat step 1 with pretty-printing (adds whitespace)
        step = json.loads(lines[0])
        pretty_line = json.dumps(step, sort_keys=True, indent=2) + "\n"
        lines[0] = pretty_line
        _write_trace_lines(artifact, lines)

        result = _run_verifier(artifact)
        assert result.returncode in (1, 2), (
            f"Expected exit 1 or 2, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        receipt = _read_receipt(artifact)
        if receipt is not None:
            assert receipt["status"] != "PASS", (
                "Verifier must never return PASS on non-canonical input"
            )


# ---------------------------------------------------------------------------
# Test C: Replay divergence (replay mismatch)
# ---------------------------------------------------------------------------

def test_replay_mismatch():
    """
    Change expected_output in input/cognitive_task.json so it no longer
    matches the trace output.
    Expected: exit 1, receipt replay_match False, status FAIL.
    """
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)

        task_path = artifact / "input" / "cognitive_task.json"
        with open(task_path) as f:
            task = json.load(f)
        task["expected_output"] = "WRONG_OUTPUT"
        with open(task_path, "w") as f:
            json.dump(task, f)

        result = _run_verifier(artifact)
        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        receipt = _read_receipt(artifact)
        assert receipt is not None, "Receipt was not written"
        assert receipt["status"] == "FAIL", (
            f"Expected receipt status FAIL, got {receipt['status']}"
        )
        assert receipt["replay_match"] is False, (
            f"Expected replay_match=False, got {receipt.get('replay_match')}"
        )


# ---------------------------------------------------------------------------
# Test D: Governance DENY
# ---------------------------------------------------------------------------

def test_governance_deny():
    """
    Replace the governance step's verdict with DENY and recompute the hash
    so the chain is structurally valid but the governance decision is DENY.
    Expected: exit 1, receipt status FAIL, governance_verdict DENY.
    """
    with tempfile.TemporaryDirectory() as tmp:
        artifact = _copy_artifact(tmp)

        lines = _read_trace_lines(artifact)
        # Find and mutate the governance_check step
        new_lines = []
        prev_hash = "0" * 64
        for raw_line in lines:
            step = json.loads(raw_line.strip())
            if step.get("action") == "governance_check":
                step["verdict"] = "DENY"
                step["prev_hash"] = prev_hash
                # Recompute hash so chain is valid (only verdict changed)
                step_without_hash = {k: v for k, v in step.items() if k != "hash"}
                step["hash"] = _sha256hex(_canonical_json(step_without_hash))
            elif "prev_hash" in step:
                # Update subsequent steps' prev_hash to maintain chain validity
                step["prev_hash"] = prev_hash
                step_without_hash = {k: v for k, v in step.items() if k != "hash"}
                step["hash"] = _sha256hex(_canonical_json(step_without_hash))
            prev_hash = step["hash"]
            new_lines.append(_canonical_json(step).decode("utf-8") + "\n")
        _write_trace_lines(artifact, new_lines)

        result = _run_verifier(artifact)
        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        receipt = _read_receipt(artifact)
        assert receipt is not None, "Receipt was not written"
        assert receipt["status"] == "FAIL", (
            f"Expected receipt status FAIL, got {receipt['status']}"
        )
        assert receipt.get("governance_verdict") == "DENY", (
            f"Expected governance_verdict=DENY, got {receipt.get('governance_verdict')}"
        )
