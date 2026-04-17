"""
CLI golden vector tests for the Tetrahedral Mesh Verifier.

Validates that the CLI correctly verifies the golden vector JSON file
and produces the expected exit codes and output.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
GOLDEN_JSON = REPO_ROOT / "tests" / "vectors" / "golden_tetra_mesh.json"
GOLDEN_SHA256 = REPO_ROOT / "tests" / "vectors" / "golden_tetra_mesh.sha256"
CLI_SCRIPT = REPO_ROOT / "cli" / "verify_tetra_mesh.py"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run the CLI script as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, str(CLI_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


class TestCLIGoldenVector:
    """The CLI must exit 0 and print PASS for the golden vector."""

    def test_cli_exits_zero_for_golden_vector(self):
        result = _run_cli(str(GOLDEN_JSON))
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_cli_stdout_contains_pass(self):
        result = _run_cli(str(GOLDEN_JSON))
        assert "PASS" in result.stdout, (
            f"Expected 'PASS' in stdout, got: {result.stdout!r}"
        )

    def test_cli_print_hash_matches_frozen_digest(self):
        frozen = GOLDEN_SHA256.read_text(encoding="utf-8").strip()
        result = _run_cli(str(GOLDEN_JSON), "--print-hash")
        assert result.returncode == 0, (
            f"CLI failed with exit code {result.returncode}.\n"
            f"stderr: {result.stderr}"
        )
        assert frozen in result.stdout, (
            f"Expected frozen digest {frozen!r} in CLI output.\n"
            f"Got stdout: {result.stdout!r}"
        )

    def test_cli_fails_for_missing_file(self):
        result = _run_cli("/nonexistent/path/mesh.json")
        assert result.returncode == 2, (
            f"Expected exit code 2 for missing file, got {result.returncode}"
        )

    def test_cli_fails_for_invalid_json(self, tmp_path):
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json {{", encoding="utf-8")
        result = _run_cli(str(bad_json))
        assert result.returncode == 2, (
            f"Expected exit code 2 for invalid JSON, got {result.returncode}"
        )

    def test_cli_fails_for_degenerate_mesh(self, tmp_path):
        degenerate = {
            "mesh_id": "degenerate_test",
            "cells": [
                {
                    "cell_id": "cell_bad",
                    "vertex_ids": ["v1", "v2", "v3", "v4"],
                    "vertices": {
                        "v1": [0, 0, 0],
                        "v2": [1, 0, 0],
                        "v3": [0, 1, 0],
                        "v4": [1, 1, 0],  # coplanar — degenerate
                    },
                    "orientation": "positive",
                    "volume": 0.0,
                }
            ],
        }
        mesh_file = tmp_path / "degenerate.json"
        mesh_file.write_text(json.dumps(degenerate), encoding="utf-8")

        result = _run_cli(str(mesh_file))
        assert result.returncode == 1, (
            f"Expected exit code 1 for degenerate mesh, got {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
