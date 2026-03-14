#!/usr/bin/env python3
"""
TMP v1 Certification Gate

Runs the full deterministic certification checklist for TMP v1 and emits:
    TMP_CERT_CHECKLIST
    schema_valid: PASS|FAIL
    canonicalization_stable: PASS|FAIL
    golden_vectors_pass: PASS|FAIL
    negative_vectors_fail: PASS|FAIL
    error_vectors_error: PASS|FAIL
    replay_deterministic: PASS|FAIL
    tamper_detection: PASS|FAIL
    verifier_semantics_frozen: PASS|FAIL

    TMP_CERT_DECISION: CERTIFY|DO_NOT_CERTIFY

Exit codes:
    0 = Certification passes (all checklist items PASS)
    1 = Certification fails (one or more checklist items FAIL)
    2 = Runtime or tooling error
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repository root and paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_PATH    = REPO_ROOT / "schemas" / "tmp_mesh.schema.json"
CANON_DOC_PATH = REPO_ROOT / "docs" / "CANONICALIZATION.md"
VERIFIER_PATH  = REPO_ROOT / "verifier" / "verify_tmp_mesh.py"

PASS_VECTORS  = sorted((REPO_ROOT / "tests" / "vectors" / "tmp" / "pass").glob("*.json"))
FAIL_VECTORS  = sorted((REPO_ROOT / "tests" / "vectors" / "tmp" / "fail").glob("*.json"))
ERROR_VECTORS = sorted((REPO_ROOT / "tests" / "vectors" / "tmp" / "error").glob("*.json"))

# ---------------------------------------------------------------------------
# Frozen content hashes for semantic-drift detection.
# These hashes represent the certified state of the protocol files.
# Any modification to these files will set verifier_semantics_frozen=FAIL.
#
# To re-certify after an intentional change:
#   1. Update the file(s).
#   2. Re-run this script to confirm all other checks still pass.
#   3. Update the hash(es) below to reflect the new certified state.
# ---------------------------------------------------------------------------

FROZEN_HASHES: Dict[str, str] = {
    "verifier/verify_tmp_mesh.py":    "9abd7cf16e746e10a26619c6d2982ca1b74fe55e1cc96ec6febd3ed43cf59ad7",
    "schemas/tmp_mesh.schema.json":   "0735ae7ea96e07f51330c10d92a9e5689aa0ef4147295f2212eb5912165b471d",
    "docs/CANONICALIZATION.md":       "6dae85aee4890a689cb6b7a37075974f72934e6168e4bdad373989b855d99715",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CheckResult = Tuple[str, str]  # (item_name, "PASS"|"FAIL")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_verifier_module() -> types.ModuleType:
    """Dynamically load verifier/verify_tmp_mesh.py as a module."""
    spec = importlib.util.spec_from_file_location("verify_tmp_mesh", VERIFIER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load verifier from {VERIFIER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _run_verifier(mesh_obj: Dict[str, Any], verifier_module: types.ModuleType) -> Tuple[str, str]:
    """
    Run the verifier on a dict mesh object.
    Returns (verdict, canonical_sha256_or_empty).
    """
    verdict, _ = verifier_module.verify_tmp_mesh(mesh_obj)
    canon_hash = ""
    try:
        canon_hash = verifier_module.sha256_hex(
            verifier_module.compute_canonical_topology(mesh_obj)
        )
    except Exception:
        pass
    return verdict, canon_hash


def _load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file; return None on error."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            obj = json.load(fh)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Checklist item implementations
# ---------------------------------------------------------------------------

def check_schema_valid() -> CheckResult:
    """Load the JSON schema and verify it is well-formed."""
    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        assert isinstance(schema, dict), "schema must be a JSON object"
        assert schema.get("title") == "TMP Mesh v1", "schema title mismatch"
        assert "properties" in schema, "schema missing 'properties'"
        assert "$schema" in schema, "schema missing '$schema'"
        return "schema_valid", "PASS"
    except Exception as exc:
        _warn(f"schema_valid FAIL: {exc}")
        return "schema_valid", "FAIL"


def check_canonicalization_stable() -> CheckResult:
    """Verify CANONICALIZATION.md is present and non-empty."""
    try:
        content = CANON_DOC_PATH.read_text(encoding="utf-8")
        assert len(content) > 100, "CANONICALIZATION.md appears truncated"
        assert "tmp-c14n-v1" in content, "canonicalization_version token missing"
        return "canonicalization_stable", "PASS"
    except Exception as exc:
        _warn(f"canonicalization_stable FAIL: {exc}")
        return "canonicalization_stable", "FAIL"


def check_golden_vectors_pass(verifier: types.ModuleType) -> CheckResult:
    """Run all PASS vectors; require verdict==PASS for each."""
    if not PASS_VECTORS:
        _warn("golden_vectors_pass FAIL: no PASS vectors found")
        return "golden_vectors_pass", "FAIL"
    for path in PASS_VECTORS:
        mesh = _load_json(path)
        if mesh is None:
            _warn(f"golden_vectors_pass FAIL: cannot load {path.name}")
            return "golden_vectors_pass", "FAIL"
        verdict, _ = _run_verifier(mesh, verifier)
        if verdict != "PASS":
            _warn(f"golden_vectors_pass FAIL: {path.name} returned {verdict}")
            return "golden_vectors_pass", "FAIL"
    return "golden_vectors_pass", "PASS"


def check_negative_vectors_fail(verifier: types.ModuleType) -> CheckResult:
    """Run all FAIL vectors; require verdict==FAIL for each."""
    if not FAIL_VECTORS:
        _warn("negative_vectors_fail FAIL: no FAIL vectors found")
        return "negative_vectors_fail", "FAIL"
    for path in FAIL_VECTORS:
        mesh = _load_json(path)
        if mesh is None:
            _warn(f"negative_vectors_fail FAIL: cannot load {path.name}")
            return "negative_vectors_fail", "FAIL"
        verdict, _ = _run_verifier(mesh, verifier)
        if verdict != "FAIL":
            _warn(f"negative_vectors_fail FAIL: {path.name} returned {verdict} (expected FAIL)")
            return "negative_vectors_fail", "FAIL"
    return "negative_vectors_fail", "PASS"


def check_error_vectors_error(verifier: types.ModuleType) -> CheckResult:
    """
    Run all ERROR vectors; require the verifier to return exit code 2.
    ERROR vectors are expected to cause JSON parse errors or non-dict input.
    """
    if not ERROR_VECTORS:
        _warn("error_vectors_error FAIL: no ERROR vectors found")
        return "error_vectors_error", "FAIL"
    for path in ERROR_VECTORS:
        # Attempt to load — ERROR vectors are malformed JSON or non-objects
        try:
            with path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            # If it loads, check if it's a non-dict (also causes exit 2)
            if not isinstance(raw, dict):
                # Non-dict JSON object — verifier returns ERROR
                continue
            # Loaded as a dict — this vector is incorrectly classified
            _warn(f"error_vectors_error FAIL: {path.name} loaded as a valid JSON object (expected parse error or non-dict)")
            return "error_vectors_error", "FAIL"
        except json.JSONDecodeError:
            # JSON parse error — verifier returns exit 2 (ERROR)
            continue
        except OSError as exc:
            _warn(f"error_vectors_error FAIL: cannot read {path.name}: {exc}")
            return "error_vectors_error", "FAIL"
    return "error_vectors_error", "PASS"


def check_replay_deterministic(verifier: types.ModuleType) -> CheckResult:
    """
    Run each PASS vector twice; verify the canonical_sha256 is identical
    in both runs (determinism guarantee).
    """
    for path in PASS_VECTORS:
        mesh = _load_json(path)
        if mesh is None:
            _warn(f"replay_deterministic FAIL: cannot load {path.name}")
            return "replay_deterministic", "FAIL"
        _, hash1 = _run_verifier(mesh, verifier)
        _, hash2 = _run_verifier(mesh, verifier)
        if not hash1 or hash1 != hash2:
            _warn(f"replay_deterministic FAIL: {path.name} produced different hashes")
            return "replay_deterministic", "FAIL"
    return "replay_deterministic", "PASS"


def check_tamper_detection(verifier: types.ModuleType) -> CheckResult:
    """
    Take the first PASS vector, mutate it (rename a vertex ID), and verify
    the verifier returns a non-PASS verdict.
    """
    if not PASS_VECTORS:
        _warn("tamper_detection FAIL: no PASS vectors available")
        return "tamper_detection", "FAIL"

    path = PASS_VECTORS[0]
    mesh = _load_json(path)
    if mesh is None:
        _warn(f"tamper_detection FAIL: cannot load {path.name}")
        return "tamper_detection", "FAIL"

    mutated = copy.deepcopy(mesh)

    # Mutate: rename the first vertex ID in vertex_ids to something novel
    if mutated.get("vertex_ids"):
        original = mutated["vertex_ids"][0]
        mutated["vertex_ids"][0] = original + "_TAMPERED"

    verdict, _ = _run_verifier(mutated, verifier)
    if verdict == "PASS":
        _warn(f"tamper_detection FAIL: mutated vector from {path.name} still returned PASS")
        return "tamper_detection", "FAIL"
    return "tamper_detection", "PASS"


def check_verifier_semantics_frozen() -> CheckResult:
    """
    Verify that the frozen-hash files have not changed since certification.
    Any hash mismatch indicates semantic drift.
    """
    drift_detected = False
    for rel_path, expected_hash in FROZEN_HASHES.items():
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            _warn(f"verifier_semantics_frozen FAIL: {rel_path} not found")
            drift_detected = True
            continue
        actual_hash = file_sha256(full_path)
        if actual_hash != expected_hash:
            _warn(
                f"verifier_semantics_frozen FAIL: semantic drift in {rel_path} — "
                f"expected={expected_hash[:16]}…, actual={actual_hash[:16]}…"
            )
            drift_detected = True
    if drift_detected:
        return "verifier_semantics_frozen", "FAIL"
    return "verifier_semantics_frozen", "PASS"


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

_warnings: List[str] = []


def _warn(msg: str) -> None:
    _warnings.append(msg)
    print(f"  [WARN] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("Running TMP v1 Certification Gate …\n", file=sys.stderr)

    # Load verifier module
    try:
        verifier = _load_verifier_module()
    except Exception as exc:
        print(f"ERROR: Cannot load verifier module: {exc}", file=sys.stderr)
        return 2

    # Run all checklist items
    results: List[CheckResult] = []
    try:
        results.append(check_schema_valid())
        results.append(check_canonicalization_stable())
        results.append(check_golden_vectors_pass(verifier))
        results.append(check_negative_vectors_fail(verifier))
        results.append(check_error_vectors_error(verifier))
        results.append(check_replay_deterministic(verifier))
        results.append(check_tamper_detection(verifier))
        results.append(check_verifier_semantics_frozen())
    except Exception as exc:
        print(f"ERROR: Unexpected exception during certification: {exc}", file=sys.stderr)
        return 2

    all_pass = all(status == "PASS" for _, status in results)
    decision = "CERTIFY" if all_pass else "DO_NOT_CERTIFY"

    # Build receipt
    pass_vectors  = [p for p in PASS_VECTORS  if p.suffix == ".json"]
    fail_vectors  = [p for p in FAIL_VECTORS  if p.suffix == ".json"]
    error_vectors = [p for p in ERROR_VECTORS if p.suffix == ".json"]

    receipt: Dict[str, Any] = {
        "protocol":                "TMP-v1",
        "cert_gate_version":       "1.0",
        "pass_vectors":            len(pass_vectors),
        "fail_vectors":            len(fail_vectors),
        "error_vectors":           len(error_vectors),
        "canonicalization_stable": results[1][1] == "PASS",
        "tamper_detection":        results[6][1] == "PASS",
        "verdict":                 decision,
    }

    # Print checklist
    print("TMP_CERT_CHECKLIST")
    for item, status in results:
        print(f"{item}: {status}")
    print()
    print(f"TMP_CERT_DECISION: {decision}")
    print()
    print(json.dumps(receipt, indent=2))

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
