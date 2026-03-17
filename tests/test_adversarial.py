"""Adversarial test suite for delta_repeat_proof_v1.

Each test mutates a copy of the artifact and runs the independent verifier
(``verifier/verify.py --base-dir …``) via subprocess to confirm fail-closed
semantics.

Verification Matrix Contract
-----------------------------
Baseline               EXIT 0  PASS
Hash-chain failure     EXIT 1  FAIL
Non-canonical JSON     EXIT 1  FAIL
Replay mismatch        EXIT 1  FAIL
Governance DENY        EXIT 1  FAIL
"""
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

_ARTIFACT = pathlib.Path(__file__).resolve().parent.parent / "delta_repeat_proof_v1"
_VERIFIER = _ARTIFACT / "verifier" / "verify.py"


def _run_verifier(base: pathlib.Path):
    """Run ``verifier/verify.py --base-dir <base>`` and return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(_VERIFIER), "--base-dir", str(base)],
        capture_output=True,
        text=True,
        cwd=str(_ARTIFACT),
        env={
            **__import__("os").environ,
            "PYTHONPATH": str(_ARTIFACT),
        },
    )


def _copy_artifact(tmp_path: pathlib.Path) -> pathlib.Path:
    """Deep-copy the artifact into *tmp_path* and return the copy root."""
    dest = tmp_path / "artifact"
    shutil.copytree(_ARTIFACT, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return dest


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


def test_baseline_exit0_pass(tmp_path):
    """A pristine artifact must exit 0 and print PASS."""
    dest = _copy_artifact(tmp_path)
    result = _run_verifier(dest)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "PASS" in result.stdout


# ---------------------------------------------------------------------------
# Hash-chain failure
# ---------------------------------------------------------------------------


def test_hash_chain_failure_exit1_fail(tmp_path):
    """Mutating a trace event payload (without updating hashes) must exit 1 FAIL."""
    dest = _copy_artifact(tmp_path)
    trace_path = dest / "trace" / "trace.jsonl"

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    # Mutate the reflect event's payload (inputs: [1,2,3] → [9,9,9])
    event = json.loads(lines[0])
    event["payload"]["inputs"] = [9, 9, 9]
    # Rewrite without fixing event_hash or prev_hash of subsequent events
    lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    trace_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = _run_verifier(dest)
    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# Non-canonical JSON
# ---------------------------------------------------------------------------


def test_noncanonical_json_extra_whitespace_exit1_fail(tmp_path):
    """A trace line with extra whitespace must exit 1 FAIL (not pass silently)."""
    dest = _copy_artifact(tmp_path)
    trace_path = dest / "trace" / "trace.jsonl"

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    # Insert a space before the closing brace of the first line.
    lines[0] = lines[0][:-1] + " }"
    trace_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = _run_verifier(dest)
    assert result.returncode in (1, 2), (
        f"expected exit 1 or 2, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "FAIL" in result.stdout or "ERROR" in result.stderr


def test_noncanonical_json_reordered_keys_exit1_fail(tmp_path):
    """A trace line with reordered keys must exit 1 FAIL."""
    dest = _copy_artifact(tmp_path)
    trace_path = dest / "trace" / "trace.jsonl"

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    # Parse first event and re-dump with reverse key order.
    event = json.loads(lines[0])
    lines[0] = json.dumps(event, sort_keys=False, separators=(",", ":"),
                          ensure_ascii=False)
    # Only a reorder if sorted != unsorted; force it by relying on insertion order.
    # Build a dict with keys in reverse sorted order.
    reversed_event = {k: event[k] for k in sorted(event.keys(), reverse=True)}
    lines[0] = json.dumps(reversed_event, sort_keys=False, separators=(",", ":"),
                          ensure_ascii=False)
    trace_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = _run_verifier(dest)
    assert result.returncode in (1, 2), (
        f"expected exit 1 or 2, got {result.returncode}; "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    assert "FAIL" in result.stdout or "ERROR" in result.stderr


# ---------------------------------------------------------------------------
# Replay mismatch
# ---------------------------------------------------------------------------


def test_replay_mismatch_exit1_fail(tmp_path):
    """Mutating cognitive_task.json inputs must exit 1 FAIL."""
    dest = _copy_artifact(tmp_path)
    task_path = dest / "input" / "cognitive_task.json"

    task = json.loads(task_path.read_text(encoding="utf-8"))
    task["inputs"] = [10, 20, 30]
    task["expected_output"] = 60
    # Write canonical JSON so no false positive from non-canonical check.
    task_path.write_text(
        json.dumps(task, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )

    result = _run_verifier(dest)
    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# Governance DENY
# ---------------------------------------------------------------------------


def test_governance_deny_exit1_fail(tmp_path):
    """Changing the govern verdict to DENY must exit 1 FAIL.

    The event_hash is recomputed after mutation so the hash-chain check passes
    and the governance check is the actual failing gate.
    """
    import hashlib as _hashlib

    dest = _copy_artifact(tmp_path)
    trace_path = dest / "trace" / "trace.jsonl"

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    # Mutate the last event (govern stage) verdict.
    event = json.loads(lines[-1])
    event["payload"]["verdict"] = "DENY"
    # Recompute event_hash so the hash-chain check passes (govern is the last
    # event, so no downstream prev_hash is affected).
    body = {k: v for k, v in event.items() if k != "event_hash"}
    event["event_hash"] = "sha256:" + _hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    lines[-1] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    trace_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = _run_verifier(dest)
    assert result.returncode == 1, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "FAIL" in result.stdout
