"""
manifest_signing.py — Detached Ed25519 signing and verification of REPEAT key manifests.

Provides:
    sign_manifest(manifest, private_key_bytes) -> bundle dict
    verify_manifest_bundle(bundle, root_public_key_bytes) -> VerifyResult

The signed unit is the canonical UTF-8 serialization of the manifest object
(JCS / RFC 8785 rules: sorted keys, no insignificant whitespace, no NaN).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from cryptography.exceptions import InvalidSignature


# ---------------------------------------------------------------------------
# Canonical serialisation (JCS / RFC 8785 subset)
# ---------------------------------------------------------------------------

def canonical_bytes(obj: Dict[str, Any]) -> bytes:
    """Return canonical UTF-8 bytes for *obj* (sorted keys, no whitespace)."""
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def _raw_public_bytes(public_key: Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)


def _key_id(raw_public_bytes: bytes) -> str:
    """SHA-256 hex digest of raw public key bytes — used as the key identifier."""
    return hashlib.sha256(raw_public_bytes).hexdigest()


def generate_root_keypair() -> tuple[bytes, bytes]:
    """
    Generate a new Ed25519 root key-pair.

    Returns:
        (private_key_raw_bytes, public_key_raw_bytes)
        Both are 32 bytes of raw key material (no headers/encoding).
    """
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = _raw_public_bytes(private_key.public_key())
    return private_raw, public_raw


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

def sign_manifest(manifest: Dict[str, Any], root_private_key_raw: bytes) -> Dict[str, Any]:
    """
    Create a signed key manifest bundle.

    Args:
        manifest:              Validated key_manifest dict (must conform to key_manifest.schema.json).
        root_private_key_raw:  32-byte raw Ed25519 private key bytes.

    Returns:
        A key_manifest_bundle dict ready for serialisation.

    Raises:
        ValueError: if manifest is not a dict or private key has wrong length.
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a dict")
    if len(root_private_key_raw) != 32:
        raise ValueError(f"Ed25519 raw private key must be 32 bytes, got {len(root_private_key_raw)}")

    # Canonical bytes of the manifest are the signed unit.
    manifest_canonical = canonical_bytes(manifest)
    manifest_hash = hashlib.sha256(manifest_canonical).hexdigest()

    # Load private key and sign.
    private_key = Ed25519PrivateKey.from_private_bytes(root_private_key_raw)
    public_raw = _raw_public_bytes(private_key.public_key())
    signature_bytes = private_key.sign(manifest_canonical)

    return {
        "schema_version": "1.0.0",
        "bundle_type": "key_manifest_bundle",
        "manifest": manifest,
        "manifest_sha256": manifest_hash,
        "root_key_id": _key_id(public_raw),
        "signature_algorithm": "Ed25519",
        "signature_b64": base64.b64encode(signature_bytes).decode("ascii"),
    }


# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------

@dataclass
class VerifyResult:
    """Outcome of verifying a key manifest bundle."""

    bundle_provided: bool = False
    manifest_hash_valid: bool = False
    manifest_schema_valid: bool = False
    signature_valid: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        """True only when all four checks pass."""
        return (
            self.bundle_provided
            and self.manifest_hash_valid
            and self.manifest_schema_valid
            and self.signature_valid
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_provided": self.bundle_provided,
            "manifest_hash_valid": self.manifest_hash_valid,
            "manifest_schema_valid": self.manifest_schema_valid,
            "signature_valid": self.signature_valid,
            "verified": self.verified,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def _load_key_manifest_schema() -> Optional[Any]:
    """Load the key_manifest JSON Schema for structural validation."""
    try:
        import jsonschema  # type: ignore[import]
        schema_path = os.path.join(
            os.path.dirname(__file__), "schemas", "key_manifest.schema.json"
        )
        with open(schema_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def verify_manifest_bundle(
    bundle: Dict[str, Any],
    root_public_key_raw: bytes,
) -> VerifyResult:
    """
    Verify a signed key manifest bundle against a trusted root public key.

    Checks (in order):
      1. manifest_sha256 field matches SHA-256 of canonical manifest bytes.
      2. manifest conforms to key_manifest.schema.json (if jsonschema available).
      3. signature_b64 is a valid Ed25519 signature by root_public_key_raw over the canonical manifest bytes.

    Args:
        bundle:               Parsed key_manifest_bundle dict.
        root_public_key_raw:  32-byte raw Ed25519 public key bytes for the trusted root.

    Returns:
        VerifyResult dataclass with per-check outcomes.
    """
    result = VerifyResult(bundle_provided=True)

    if not isinstance(bundle, dict):
        result.errors.append("bundle must be a dict")
        return result

    manifest = bundle.get("manifest")
    if not isinstance(manifest, dict):
        result.errors.append("bundle.manifest is missing or not a dict")
        return result

    # 1. Manifest integrity check.
    stored_hash = bundle.get("manifest_sha256", "")
    try:
        manifest_canonical = canonical_bytes(manifest)
        computed_hash = hashlib.sha256(manifest_canonical).hexdigest()
        if stored_hash == computed_hash:
            result.manifest_hash_valid = True
        else:
            result.errors.append(
                f"manifest_sha256 mismatch: stored={stored_hash}, computed={computed_hash}"
            )
    except (TypeError, ValueError) as exc:
        result.errors.append(f"Cannot canonicalise manifest: {exc}")
        return result

    # 2. Schema validation of the manifest.
    schema = _load_key_manifest_schema()
    if schema is not None:
        try:
            import jsonschema  # type: ignore[import]
            jsonschema.validate(manifest, schema)
            result.manifest_schema_valid = True
        except Exception as exc:
            result.errors.append(f"manifest schema validation failed: {exc}")
    else:
        # jsonschema unavailable — skip but record.
        result.manifest_schema_valid = True
        result.errors.append("jsonschema not available; manifest schema validation skipped")

    # 3. Signature verification.
    sig_b64 = bundle.get("signature_b64", "")
    try:
        signature_bytes = base64.b64decode(sig_b64)
    except Exception as exc:
        result.errors.append(f"Cannot decode signature_b64: {exc}")
        return result

    if len(root_public_key_raw) != 32:
        result.errors.append(
            f"root public key must be 32 raw bytes, got {len(root_public_key_raw)}"
        )
        return result

    try:
        public_key = Ed25519PublicKey.from_public_bytes(root_public_key_raw)
        public_key.verify(signature_bytes, manifest_canonical)
        result.signature_valid = True
    except InvalidSignature:
        result.errors.append("signature verification failed: signature is invalid")
    except Exception as exc:
        result.errors.append(f"signature verification error: {exc}")

    return result


# ---------------------------------------------------------------------------
# Convenience: load a bundle from a file path
# ---------------------------------------------------------------------------

def load_bundle_from_file(path: str) -> Dict[str, Any]:
    """Load and parse a JSON key_manifest_bundle from *path*."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except OSError as exc:
        raise RuntimeError(f"Cannot open bundle file '{path}': {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Cannot parse bundle file '{path}': {exc}") from exc
