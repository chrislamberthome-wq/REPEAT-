#!/usr/bin/env python3
"""Verification matrix runner for delta_repeat_proof_v1.

Automates three categories of verification and outputs structured JSON:
  1. Baseline     – clean run, must exit 0 and print PASS.
  2. Determinism  – two independent runs produce identical trace SHA-256.
  3. Adversarial  – tamper cases, each must fail-closed (exit 1 or 2).

Usage::

    python scripts/run_verification_matrix.py [--json-output PATH]

Exit codes
----------
0  All checks passed.
1  One or more checks failed.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ARTIFACT = _REPO_ROOT / "delta_repeat_proof_v1"
_VERIFIER = _ARTIFACT / "verifier" / "verify.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_verifier(base: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_VERIFIER), "--base-dir", str(base)],
        capture_output=True,
        text=True,
        cwd=str(_ARTIFACT),
        env={**os.environ, "PYTHONPATH": str(_ARTIFACT)},
    )


def _copy_artifact(dest: pathlib.Path) -> pathlib.Path:
    artifact_copy = dest / "artifact"
    shutil.copytree(
        _ARTIFACT,
        artifact_copy,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    return artifact_copy


def _trace_sha256(base: pathlib.Path) -> str:
    trace_bytes = (base / "trace" / "trace.jsonl").read_bytes()
    return "sha256:" + hashlib.sha256(trace_bytes).hexdigest()


def _check(name: str, passed: bool, detail: str) -> Dict[str, Any]:
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}: {detail}")
    return {"name": name, "status": status, "detail": detail}


# ---------------------------------------------------------------------------
# 1. Baseline
# ---------------------------------------------------------------------------


def run_baseline() -> List[Dict[str, Any]]:
    print("\n[1] Baseline validation")
    results = []
    with tempfile.TemporaryDirectory() as td:
        base = _copy_artifact(pathlib.Path(td))
        proc = _run_verifier(base)
        ok = proc.returncode == 0 and "PASS" in proc.stdout
        results.append(_check(
            "baseline_exit0_pass",
            ok,
            f"exit={proc.returncode} stdout={proc.stdout.strip()!r}",
        ))
    return results


# ---------------------------------------------------------------------------
# 2. Determinism
# ---------------------------------------------------------------------------


def run_determinism() -> List[Dict[str, Any]]:
    print("\n[2] Determinism validation")
    results = []
    hashes = []
    for run_n in (1, 2):
        with tempfile.TemporaryDirectory() as td:
            base = _copy_artifact(pathlib.Path(td))
            proc = _run_verifier(base)
            h = _trace_sha256(base)
            hashes.append(h)
            ok = proc.returncode == 0
            results.append(_check(
                f"determinism_run_{run_n}",
                ok,
                f"exit={proc.returncode} trace_sha256={h}",
            ))
    if len(hashes) == 2:
        match = hashes[0] == hashes[1]
        results.append(_check(
            "determinism_hashes_identical",
            match,
            f"run1={hashes[0]} run2={hashes[1]}",
        ))
    return results


# ---------------------------------------------------------------------------
# 3. Adversarial
# ---------------------------------------------------------------------------


def _mutate_hash_chain(base: pathlib.Path) -> None:
    trace = base / "trace" / "trace.jsonl"
    lines = trace.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[0])
    event["payload"]["inputs"] = [9, 9, 9]
    lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    trace.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mutate_noncanonical(base: pathlib.Path) -> None:
    trace = base / "trace" / "trace.jsonl"
    lines = trace.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0][:-1] + " }"
    trace.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _mutate_replay(base: pathlib.Path) -> None:
    task = base / "input" / "cognitive_task.json"
    obj = json.loads(task.read_text(encoding="utf-8"))
    obj["inputs"] = [10, 20, 30]
    obj["expected_output"] = 60
    task.write_text(
        json.dumps(obj, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _mutate_governance_deny(base: pathlib.Path) -> None:
    trace = base / "trace" / "trace.jsonl"
    lines = trace.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[-1])
    event["payload"]["verdict"] = "DENY"
    # Recompute event_hash so hash-chain passes and governance check fires.
    body = {k: v for k, v in event.items() if k != "event_hash"}
    event["event_hash"] = "sha256:" + hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    lines[-1] = json.dumps(event, sort_keys=True, separators=(",", ":"))
    trace.write_text("\n".join(lines) + "\n", encoding="utf-8")


_ADVERSARIAL_CASES = [
    ("hash_chain_failure",   _mutate_hash_chain,        (1,)),
    ("noncanonical_json",    _mutate_noncanonical,       (1, 2)),
    ("replay_mismatch",      _mutate_replay,             (1,)),
    ("governance_deny",      _mutate_governance_deny,    (1,)),
]


def run_adversarial() -> List[Dict[str, Any]]:
    print("\n[3] Adversarial mutation checks")
    results = []
    for case_name, mutate_fn, expected_exits in _ADVERSARIAL_CASES:
        with tempfile.TemporaryDirectory() as td:
            base = _copy_artifact(pathlib.Path(td))
            mutate_fn(base)
            proc = _run_verifier(base)
            ok = proc.returncode in expected_exits
            results.append(_check(
                f"adversarial_{case_name}",
                ok,
                (
                    f"exit={proc.returncode} "
                    f"expected={expected_exits} "
                    f"stdout={proc.stdout.strip()!r}"
                ),
            ))
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-output",
        metavar="PATH",
        help="Write structured JSON results to this file.",
    )
    args = parser.parse_args()

    print("=== Verification Matrix: delta_repeat_proof_v1 ===")

    all_results: List[Dict[str, Any]] = []
    all_results += run_baseline()
    all_results += run_determinism()
    all_results += run_adversarial()

    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL")
    total = len(all_results)

    print(f"\n=== Summary: {passed}/{total} passed, {failed} failed ===")

    matrix = {
        "artifact": "delta_repeat_proof_v1",
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": all_results,
    }

    if args.json_output:
        out = pathlib.Path(args.json_output)
        out.write_text(json.dumps(matrix, indent=2), encoding="utf-8")
        print(f"JSON output written to {out}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
