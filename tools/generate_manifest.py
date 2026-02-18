#!/usr/bin/env python3
"""
Generate SHA-256 manifest for CRC-16/CCITT-FALSE certification.

This script calculates SHA-256 checksums for all certified files and
creates a manifest for immutability verification.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_manifest(repo_root: Path) -> dict:
    """Generate manifest with SHA-256 checksums of certified files."""
    
    certified_files = {
        "vectors": "audit/golden/crc16_ccitt_false.vectors.json",
        "implementation": "tools/crc16_ccitt_false.py",
        "documentation": "docs/CRC16_REPRO.md",
    }
    
    manifest = {
        "version": "1.0.0",
        "algorithm": "CRC-16/CCITT-FALSE",
        "generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "checksums": {},
        "files": []
    }
    
    for label, rel_path in certified_files.items():
        filepath = repo_root / rel_path
        if not filepath.exists():
            print(f"ERROR: Required file not found: {rel_path}", file=sys.stderr)
            sys.exit(1)
        
        checksum = calculate_sha256(filepath)
        manifest["checksums"][label] = checksum
        manifest["files"].append({
            "label": label,
            "path": rel_path,
            "sha256": checksum
        })
    
    return manifest


def main():
    """Main entry point."""
    # Determine repository root
    script_dir = Path(__file__).parent.absolute()
    repo_root = script_dir.parent
    
    # Generate manifest
    manifest = generate_manifest(repo_root)
    
    # Write manifest file
    manifest_path = repo_root / "audit" / "golden" / "crc16_ccitt_false.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")  # Add trailing newline
    
    print(f"✓ Manifest generated: {manifest_path.relative_to(repo_root)}")
    print(f"  Files certified: {len(manifest['files'])}")
    for file_info in manifest["files"]:
        print(f"    - {file_info['label']:20s}: {file_info['sha256'][:16]}...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
