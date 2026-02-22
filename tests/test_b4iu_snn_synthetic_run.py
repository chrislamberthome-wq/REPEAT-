"""Tests for B4IU-SNN v0.1 synthetic conformance run."""

import os
import subprocess
import sys

import pytest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(args, **kwargs):
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        **kwargs,
    )


class TestB4IUSNNSyntheticRun:
    """End-to-end: emit synthetic run and verify it passes."""

    def test_emit_and_verify_pass(self, tmp_path):
        run_dir = str(tmp_path / "b4iu_snn_synthetic_run")

        # Emit
        result = _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", run_dir])
        assert result.returncode == 0, f"Emitter failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

        # Verify
        result = _run([sys.executable, "-m", "verifier.b4iu_snn_verify", run_dir])
        assert result.returncode == 0, f"Verifier failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        assert "PASS" in result.stdout

    def test_emit_produces_required_artifacts(self, tmp_path):
        run_dir = str(tmp_path / "b4iu_snn_synthetic_run")
        _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", run_dir])

        required = {"manifest.json", "policy.json", "trace.jsonl", "receipt.json", "verdict.json"}
        actual = {f for f in os.listdir(run_dir) if os.path.isfile(os.path.join(run_dir, f))}
        assert required == actual

    def test_emit_is_deterministic(self, tmp_path):
        """Two successive emits to different dirs produce identical artifacts."""
        import json

        dir_a = str(tmp_path / "run_a")
        dir_b = str(tmp_path / "run_b")
        _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", dir_a])
        _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", dir_b])

        for name in ["manifest.json", "policy.json", "receipt.json", "verdict.json"]:
            with open(os.path.join(dir_a, name)) as fa, open(os.path.join(dir_b, name)) as fb:
                assert json.load(fa) == json.load(fb), f"{name} not deterministic"

        with open(os.path.join(dir_a, "trace.jsonl")) as fa:
            lines_a = fa.readlines()
        with open(os.path.join(dir_b, "trace.jsonl")) as fb:
            lines_b = fb.readlines()
        assert lines_a == lines_b, "trace.jsonl not deterministic"

    def test_verifier_fails_on_missing_artifact(self, tmp_path):
        run_dir = str(tmp_path / "b4iu_snn_synthetic_run")
        _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", run_dir])
        os.remove(os.path.join(run_dir, "verdict.json"))
        result = _run([sys.executable, "-m", "verifier.b4iu_snn_verify", run_dir])
        assert result.returncode != 0
        assert "FAIL" in result.stderr

    def test_verifier_fails_on_tampered_trace(self, tmp_path):
        import json

        run_dir = str(tmp_path / "b4iu_snn_synthetic_run")
        _run([sys.executable, "-m", "tools.b4iu_snn_emit_synthetic_run", run_dir])

        trace_path = os.path.join(run_dir, "trace.jsonl")
        with open(trace_path) as f:
            lines = f.readlines()

        # Corrupt the first event's hash
        event = json.loads(lines[0])
        event["hash"] = "sha256:" + "a" * 64
        lines[0] = json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
        with open(trace_path, "w") as f:
            f.writelines(lines)

        result = _run([sys.executable, "-m", "verifier.b4iu_snn_verify", run_dir])
        assert result.returncode != 0
        assert "FAIL" in result.stderr
