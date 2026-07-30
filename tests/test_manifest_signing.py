"""
Tests for manifest_signing.py — detached Ed25519 sign/verify of key manifests,
and for verify_run.py — receipt verifier with signed manifest bundle support.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict

import pytest

from manifest_signing import (
    VerifyResult,
    canonical_bytes,
    generate_root_keypair,
    load_bundle_from_file,
    sign_manifest,
    verify_manifest_bundle,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_manifest(num_keys: int = 1) -> Dict[str, Any]:
    """Create a minimal valid key_manifest dict for testing."""
    keys = []
    for i in range(num_keys):
        # Deterministic fake key bytes (not real Ed25519, but valid for schema).
        raw = bytes(range(i, i + 32))
        kid = hashlib.sha256(raw).hexdigest()
        pub_b64 = base64.b64encode(raw).decode("ascii")
        keys.append(
            {
                "key_id": kid,
                "algorithm": "Ed25519",
                "public_key_b64": pub_b64,
                "purpose": f"test key {i}",
                "added_at": "2026-01-01T00:00:00Z",
            }
        )
    return {
        "schema_version": "1.0.0",
        "manifest_type": "key_manifest",
        "created_at": "2026-01-01T00:00:00Z",
        "description": "Test manifest",
        "keys": keys,
    }


@pytest.fixture()
def root_keypair():
    """Return (private_raw, public_raw) for a freshly-generated root key."""
    return generate_root_keypair()


@pytest.fixture()
def valid_bundle(root_keypair):
    priv, _pub = root_keypair
    manifest = _make_manifest()
    return sign_manifest(manifest, priv), root_keypair


# ---------------------------------------------------------------------------
# canonical_bytes
# ---------------------------------------------------------------------------

class TestCanonicalBytes:
    def test_deterministic(self):
        obj = {"b": 2, "a": 1}
        assert canonical_bytes(obj) == canonical_bytes(obj)

    def test_sorted_keys(self):
        result = canonical_bytes({"z": 9, "a": 1})
        assert result == b'{"a":1,"z":9}'

    def test_utf8_output(self):
        result = canonical_bytes({"k": "café"})
        assert isinstance(result, bytes)
        assert result.decode("utf-8") == '{"k":"café"}'

    def test_no_nan_raises(self):
        import math
        with pytest.raises((ValueError, TypeError)):
            canonical_bytes({"v": math.nan})


# ---------------------------------------------------------------------------
# generate_root_keypair
# ---------------------------------------------------------------------------

class TestGenerateRootKeypair:
    def test_returns_32_byte_keys(self):
        priv, pub = generate_root_keypair()
        assert len(priv) == 32
        assert len(pub) == 32

    def test_unique_per_call(self):
        priv1, pub1 = generate_root_keypair()
        priv2, pub2 = generate_root_keypair()
        assert priv1 != priv2
        assert pub1 != pub2


# ---------------------------------------------------------------------------
# sign_manifest
# ---------------------------------------------------------------------------

class TestSignManifest:
    def test_bundle_structure(self, root_keypair):
        priv, pub = root_keypair
        manifest = _make_manifest()
        bundle = sign_manifest(manifest, priv)

        assert bundle["schema_version"] == "1.0.0"
        assert bundle["bundle_type"] == "key_manifest_bundle"
        assert bundle["manifest"] == manifest
        assert len(bundle["manifest_sha256"]) == 64
        assert len(bundle["root_key_id"]) == 64
        assert bundle["signature_algorithm"] == "Ed25519"
        assert len(bundle["signature_b64"]) > 0

    def test_manifest_sha256_correct(self, root_keypair):
        priv, _ = root_keypair
        manifest = _make_manifest()
        bundle = sign_manifest(manifest, priv)
        expected = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
        assert bundle["manifest_sha256"] == expected

    def test_root_key_id_matches_public_key(self, root_keypair):
        priv, pub = root_keypair
        manifest = _make_manifest()
        bundle = sign_manifest(manifest, priv)
        expected_kid = hashlib.sha256(pub).hexdigest()
        assert bundle["root_key_id"] == expected_kid

    def test_signature_is_base64(self, root_keypair):
        priv, _ = root_keypair
        bundle = sign_manifest(_make_manifest(), priv)
        decoded = base64.b64decode(bundle["signature_b64"])
        assert len(decoded) == 64  # Ed25519 signatures are always 64 bytes

    def test_invalid_manifest_type_raises(self, root_keypair):
        priv, _ = root_keypair
        with pytest.raises(ValueError, match="dict"):
            sign_manifest("not a dict", priv)  # type: ignore[arg-type]

    def test_wrong_key_length_raises(self):
        with pytest.raises(ValueError, match="32 bytes"):
            sign_manifest(_make_manifest(), b"short")

    def test_deterministic_hash_same_manifest(self, root_keypair):
        priv, _ = root_keypair
        manifest = _make_manifest()
        b1 = sign_manifest(manifest, priv)
        b2 = sign_manifest(manifest, priv)
        # Hash must be identical for same manifest.
        assert b1["manifest_sha256"] == b2["manifest_sha256"]


# ---------------------------------------------------------------------------
# verify_manifest_bundle
# ---------------------------------------------------------------------------

class TestVerifyManifestBundle:
    def test_valid_bundle_passes(self, valid_bundle):
        bundle, (_, pub) = valid_bundle
        result = verify_manifest_bundle(bundle, pub)
        assert result.verified
        assert result.bundle_provided
        assert result.manifest_hash_valid
        assert result.manifest_schema_valid
        assert result.signature_valid
        assert result.errors == [] or all(
            "skipped" in e for e in result.errors
        )

    def test_wrong_public_key_fails(self, valid_bundle):
        bundle, _ = valid_bundle
        _, other_pub = generate_root_keypair()
        result = verify_manifest_bundle(bundle, other_pub)
        assert not result.verified
        assert not result.signature_valid
        assert any("invalid" in e.lower() or "failed" in e.lower() for e in result.errors)

    def test_tampered_manifest_sha256_fails(self, valid_bundle):
        bundle, (_, pub) = valid_bundle
        tampered = dict(bundle)
        tampered["manifest_sha256"] = "a" * 64
        result = verify_manifest_bundle(tampered, pub)
        assert not result.manifest_hash_valid

    def test_tampered_manifest_content_fails(self, valid_bundle):
        bundle, (_, pub) = valid_bundle
        tampered = dict(bundle)
        tampered_manifest = dict(tampered["manifest"])
        tampered_manifest["description"] = "tampered"
        tampered["manifest"] = tampered_manifest
        result = verify_manifest_bundle(tampered, pub)
        # Hash will no longer match AND signature will fail.
        assert not result.verified

    def test_tampered_signature_fails(self, valid_bundle):
        bundle, (_, pub) = valid_bundle
        tampered = dict(bundle)
        bad_sig = base64.b64encode(b"\x00" * 64).decode("ascii")
        tampered["signature_b64"] = bad_sig
        result = verify_manifest_bundle(tampered, pub)
        assert not result.signature_valid

    def test_non_dict_bundle_returns_error(self, root_keypair):
        _, pub = root_keypair
        result = verify_manifest_bundle("not a dict", pub)  # type: ignore[arg-type]
        assert not result.verified
        assert result.errors

    def test_missing_manifest_key_returns_error(self, root_keypair):
        _, pub = root_keypair
        result = verify_manifest_bundle({}, pub)
        assert not result.verified

    def test_wrong_key_length_returns_error(self, valid_bundle):
        bundle, _ = valid_bundle
        result = verify_manifest_bundle(bundle, b"too_short")
        assert not result.verified
        assert any("32" in e for e in result.errors)

    def test_verify_result_to_dict(self, valid_bundle):
        bundle, (_, pub) = valid_bundle
        result = verify_manifest_bundle(bundle, pub)
        d = result.to_dict()
        assert "verified" in d
        assert "bundle_provided" in d
        assert "manifest_hash_valid" in d
        assert "manifest_schema_valid" in d
        assert "signature_valid" in d
        assert "errors" in d


# ---------------------------------------------------------------------------
# load_bundle_from_file
# ---------------------------------------------------------------------------

class TestLoadBundleFromFile:
    def test_round_trip(self, root_keypair, tmp_path):
        priv, _ = root_keypair
        bundle = sign_manifest(_make_manifest(), priv)
        path = tmp_path / "bundle.json"
        path.write_text(json.dumps(bundle), encoding="utf-8")
        loaded = load_bundle_from_file(str(path))
        assert loaded == bundle

    def test_missing_file_raises(self):
        with pytest.raises(RuntimeError, match="Cannot open"):
            load_bundle_from_file("/nonexistent/path/bundle.json")

    def test_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        with pytest.raises(RuntimeError, match="Cannot parse"):
            load_bundle_from_file(str(path))


# ---------------------------------------------------------------------------
# VerifyResult dataclass
# ---------------------------------------------------------------------------

class TestVerifyResult:
    def test_verified_true_when_all_pass(self):
        vr = VerifyResult(
            bundle_provided=True,
            manifest_hash_valid=True,
            manifest_schema_valid=True,
            signature_valid=True,
        )
        assert vr.verified

    def test_verified_false_when_any_fails(self):
        vr = VerifyResult(
            bundle_provided=True,
            manifest_hash_valid=True,
            manifest_schema_valid=True,
            signature_valid=False,
        )
        assert not vr.verified

    def test_default_not_verified(self):
        vr = VerifyResult()
        assert not vr.verified


# ---------------------------------------------------------------------------
# verify_run.py CLI integration
# ---------------------------------------------------------------------------

class TestVerifyRunCLI:
    """Integration tests for verify_run.py via subprocess."""

    def _run(self, *args: str) -> "subprocess.CompletedProcess[str]":
        return subprocess.run(
            [sys.executable, "verify_run.py", *args],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )

    def _write_receipts(self, tmp_path, receipts):
        """Write a list of receipt dicts to a JSONL file."""
        p = tmp_path / "receipts.jsonl"
        lines = [json.dumps(r) for r in receipts]
        p.write_text("\n".join(lines), encoding="utf-8")
        return str(p)

    def _make_receipt(self, run_id: int = 1, verdict_pass: bool = True):
        """Build a minimal valid spintronics receipt."""
        import hashlib as _hl

        packet = {
            "schema": "repeat-spintronics-packet-v1",
            "device_baseline": {
                "device_id": "TEST",
                "baseline_resistance_parallel_ohms": 1000.0,
                "baseline_resistance_antiparallel_ohms": 1500.0,
                "temperature_celsius": 25.0,
            },
        }
        packet_hash = "sha256:" + _hl.sha256(
            json.dumps(packet, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        base = {
            "schema": "repeat-spintronics-receipt-v1",
            "packet_hash_sha256": packet_hash,
            "run_id": run_id,
            "measured_resistance_ohms": 1001.0,
            "verdict": {"pass": verdict_pass},
            "metrics": {"mean_resistance_ohms": 1000.0, "drift_pct": 0.1},
        }
        if not verdict_pass:
            base["verdict"]["fail_reason"] = "drift_detected"

        # evidence hash
        ev_hash = "sha256:" + _hl.sha256(
            json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        base["evidence_hash_sha256"] = ev_hash

        # receipt hash
        rc_hash = "sha256:" + _hl.sha256(
            json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        base["receipt_hash_sha256"] = rc_hash
        return base

    # -- no manifest tests ------------------------------------------------

    def test_no_args_exits_nonzero(self):
        r = subprocess.run(
            [sys.executable, "verify_run.py"],
            capture_output=True,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."),
        )
        assert r.returncode != 0

    def test_missing_receipts_file_exits_2(self, tmp_path):
        r = self._run("/nonexistent/receipts.jsonl")
        assert r.returncode == 2

    def test_manifest_bundle_without_root_key_exits_2(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        r = self._run(str(p), "--manifest-bundle", "some.json")
        assert r.returncode == 2

    def test_root_key_without_manifest_bundle_exits_2(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        r = self._run(str(p), "--root-public-key", "some.key")
        assert r.returncode == 2

    # -- with valid manifest bundle ----------------------------------------

    def test_valid_bundle_valid_receipts_passes(self, tmp_path):
        priv, pub = generate_root_keypair()
        bundle = sign_manifest(_make_manifest(), priv)

        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

        key_path = tmp_path / "root.key"
        key_path.write_bytes(pub)

        receipts_path = self._write_receipts(tmp_path, [self._make_receipt()])
        r = self._run(
            receipts_path,
            "--manifest-bundle", str(bundle_path),
            "--root-public-key", str(key_path),
        )
        assert r.returncode == 0

    def test_invalid_bundle_signature_exits_1(self, tmp_path):
        priv, pub = generate_root_keypair()
        _, other_priv = generate_root_keypair()  # wrong signer

        bundle = sign_manifest(_make_manifest(), other_priv)  # signed with wrong key
        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

        key_path = tmp_path / "root.key"
        key_path.write_bytes(pub)

        receipts_path = self._write_receipts(tmp_path, [self._make_receipt()])
        r = self._run(
            receipts_path,
            "--manifest-bundle", str(bundle_path),
            "--root-public-key", str(key_path),
        )
        assert r.returncode == 1

    def test_emit_receipt_outputs_json(self, tmp_path):
        priv, pub = generate_root_keypair()
        bundle = sign_manifest(_make_manifest(), priv)

        bundle_path = tmp_path / "bundle.json"
        bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
        key_path = tmp_path / "root.key"
        key_path.write_bytes(pub)

        receipts_path = self._write_receipts(tmp_path, [self._make_receipt()])
        r = self._run(
            receipts_path,
            "--manifest-bundle", str(bundle_path),
            "--root-public-key", str(key_path),
            "--emit-receipt",
        )
        assert r.returncode == 0
        # stdout should contain valid JSON
        parsed = json.loads(r.stdout)
        assert parsed["receipt_type"] == "verification_receipt"
        assert parsed["signed_manifest_provided"] is True
        assert parsed["manifest_cryptographically_verified"] is True
        assert parsed["artifact_signature_policy_enforced"] is True

    def test_no_manifest_emit_receipt_shows_not_authenticated(self, tmp_path):
        receipts_path = self._write_receipts(tmp_path, [self._make_receipt()])
        r = self._run(receipts_path, "--emit-receipt")
        assert r.returncode == 0
        parsed = json.loads(r.stdout)
        assert parsed["signed_manifest_provided"] is False
        assert parsed["manifest_cryptographically_verified"] is False
        assert parsed["artifact_signature_policy_enforced"] is False
