#!/usr/bin/env python3
"""
Verify SHA-256 manifest for CRC-16/CCITT-FALSE certification.

This script validates that certified files have not been modified by
comparing their current SHA-256 checksums against the manifest.
"""

import hashlib
import json
import sys
from pathlib import Path


def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_manifest(repo_root: Path) -> bool:
    """Verify all files in manifest match their expected checksums."""
    
    manifest_path = repo_root / "audit" / "golden" / "crc16_ccitt_false.manifest.json"
    
    if not manifest_path.exists():
        print(f"✗ ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        return False
    
    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    print(f"Verifying CRC-16/CCITT-FALSE certification manifest")
    print(f"Version: {manifest['version']}")
    print(f"Generated: {manifest['generated']}")
    print("=" * 70)
    
    all_valid = True
    for file_info in manifest["files"]:
        label = file_info["label"]
        rel_path = file_info["path"]
        expected_checksum = file_info["sha256"]
        
        filepath = repo_root / rel_path
        
        if not filepath.exists():
            print(f"✗ {label:20s}: FILE NOT FOUND ({rel_path})")
            all_valid = False
            continue
        
        actual_checksum = calculate_sha256(filepath)
        
        if actual_checksum == expected_checksum:
            print(f"✓ {label:20s}: {actual_checksum[:16]}... OK")
        else:
            print(f"✗ {label:20s}: CHECKSUM MISMATCH")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            all_valid = False
    
    print("=" * 70)
    if all_valid:
        print("✓ All files verified successfully")
        return True
    else:
        print("✗ Verification FAILED - files have been modified!")
        return False


def main():
    """Main entry point."""
    # Determine repository root
    script_dir = Path(__file__).parent.absolute()
    repo_root = script_dir.parent
    
    # Verify manifest
    success = verify_manifest(repo_root)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
