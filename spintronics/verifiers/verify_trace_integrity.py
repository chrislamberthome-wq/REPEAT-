#!/usr/bin/env python3
"""Verify pulse trace integrity for spintronics experiments.

This verifier checks pulse sequence data for integrity,
validates checksums, and ensures trace consistency.
"""

import json
import sys
import hashlib
from typing import Dict, Any, List, Tuple


def compute_trace_checksum(pulse_sequence: List[Dict[str, Any]], 
                          algorithm: str = 'sha256') -> str:
    """
    Compute checksum of pulse trace.
    
    Creates canonical JSON representation of pulse sequence
    and computes its hash.
    
    Args:
        pulse_sequence: List of pulse dictionaries
        algorithm: Hash algorithm ('sha256', 'crc32', 'md5')
        
    Returns:
        Hexadecimal checksum string
    """
    # Create canonical JSON (sorted keys, no whitespace)
    canonical = json.dumps(pulse_sequence, sort_keys=True, separators=(',', ':'))
    
    if algorithm == 'sha256':
        hasher = hashlib.sha256()
    elif algorithm == 'md5':
        hasher = hashlib.md5()
    elif algorithm == 'crc32':
        import zlib
        checksum = zlib.crc32(canonical.encode('utf-8')) & 0xffffffff
        return f"{checksum:08x}"
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    hasher.update(canonical.encode('utf-8'))
    return hasher.hexdigest()


def verify_pulse_sequence(pulse_sequence: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Verify pulse sequence validity.
    
    Checks:
    - Pulse indices are sequential
    - All required fields present
    - Valid pulse types
    - Non-negative durations
    
    Args:
        pulse_sequence: List of pulse dictionaries
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if not pulse_sequence:
        errors.append("Empty pulse sequence")
        return False, errors
    
    for i, pulse in enumerate(pulse_sequence):
        # Check index
        expected_index = i
        if pulse.get("index") != expected_index:
            errors.append(f"Pulse index mismatch at position {i}: expected {expected_index}, got {pulse.get('index')}")
        
        # Check required fields
        required_fields = ["index", "amplitude", "duration", "pulse_type"]
        for field in required_fields:
            if field not in pulse:
                errors.append(f"Missing field '{field}' in pulse {i}")
        
        # Check pulse type
        valid_types = ["write", "read", "reset", "idle"]
        if pulse.get("pulse_type") not in valid_types:
            errors.append(f"Invalid pulse type in pulse {i}: {pulse.get('pulse_type')}")
        
        # Check non-negative duration
        duration = pulse.get("duration", -1)
        if duration < 0:
            errors.append(f"Negative duration in pulse {i}: {duration}")
    
    return len(errors) == 0, errors


def verify_trace_integrity(packet: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify complete trace integrity.
    
    Checks pulse sequence validity and verifies checksum.
    
    Args:
        packet: Trace integrity packet
        
    Returns:
        Tuple of (is_valid, verification_details)
    """
    errors = []
    
    # Check schema version
    if packet.get("schema_version") != "trace_integrity_v1":
        errors.append("Invalid schema version")
        return False, {"errors": errors}
    
    # Get pulse sequence
    pulse_sequence = packet.get("pulse_sequence", [])
    
    # Verify pulse sequence structure
    is_valid, pulse_errors = verify_pulse_sequence(pulse_sequence)
    if not is_valid:
        return False, {"errors": pulse_errors}
    
    # Verify integrity check
    integrity = packet.get("integrity_check", {})
    expected_checksum = integrity.get("checksum", "")
    algorithm = integrity.get("checksum_algorithm", "sha256")
    
    # Compute actual checksum
    computed_checksum = compute_trace_checksum(pulse_sequence, algorithm)
    
    # Verify checksum match
    checksum_valid = computed_checksum == expected_checksum
    
    # Compute total duration
    total_duration = sum(p.get("duration", 0) for p in pulse_sequence)
    
    # Check pulse count
    pulse_count = len(pulse_sequence)
    expected_count = integrity.get("pulse_count")
    count_valid = expected_count is None or pulse_count == expected_count
    
    # Check total duration
    expected_duration = integrity.get("total_duration")
    duration_valid = expected_duration is None or abs(total_duration - expected_duration) < 1e-6
    
    details = {
        "checksum_valid": checksum_valid,
        "computed_checksum": computed_checksum,
        "expected_checksum": expected_checksum,
        "total_duration": total_duration,
        "pulse_count": pulse_count,
        "count_valid": count_valid,
        "duration_valid": duration_valid,
    }
    
    overall_valid = checksum_valid and count_valid and duration_valid
    
    return overall_valid, details


def main():
    """Main entry point for verification script."""
    if len(sys.argv) < 2:
        print("Usage: verify_trace_integrity.py <trace_file.json>", file=sys.stderr)
        return 1
    
    trace_file = sys.argv[1]
    
    try:
        with open(trace_file, 'r') as f:
            packet = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading trace: {e}", file=sys.stderr)
        return 1
    
    # Verify trace
    is_valid, details = verify_trace_integrity(packet)
    
    if is_valid:
        print("TRACE INTEGRITY VERIFIED")
        print(f"  Checksum: {details['computed_checksum'][:16]}...")
        print(f"  Pulse count: {details['pulse_count']}")
        print(f"  Total duration: {details['total_duration']:.2f} ns")
        return 0
    else:
        print("TRACE INTEGRITY VERIFICATION FAILED", file=sys.stderr)
        if not details.get("checksum_valid", True):
            print(f"  Checksum mismatch", file=sys.stderr)
            print(f"    Expected: {details['expected_checksum'][:16]}...", file=sys.stderr)
            print(f"    Computed: {details['computed_checksum'][:16]}...", file=sys.stderr)
        if not details.get("count_valid", True):
            print(f"  Pulse count mismatch", file=sys.stderr)
        if not details.get("duration_valid", True):
            print(f"  Duration mismatch", file=sys.stderr)
        if "errors" in details:
            for error in details["errors"]:
                print(f"  - {error}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
