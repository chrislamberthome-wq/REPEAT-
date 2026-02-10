#!/usr/bin/env python3
"""Verify MRAM write/read operations with threshold-based state detection.

This verifier validates MRAM receipts by checking write/read consistency,
threshold-based resistance decoding, and switching margin verification.
"""

import json
import sys
from typing import Dict, Any, Tuple, List


def decode_resistance_to_bit(resistance: float, 
                            low_threshold: float,
                            high_threshold: float) -> Tuple[int, bool]:
    """
    Decode resistance value to bit using threshold comparison.
    
    Low resistance (< midpoint) -> bit 0 (parallel state)
    High resistance (> midpoint) -> bit 1 (antiparallel state)
    
    Args:
        resistance: Measured resistance in ohms
        low_threshold: Low resistance state threshold
        high_threshold: High resistance state threshold
        
    Returns:
        Tuple of (decoded_bit, is_valid)
        is_valid is False if resistance is in ambiguous region
    """
    midpoint = (low_threshold + high_threshold) / 2.0
    margin = (high_threshold - low_threshold) / 4.0
    
    # Check if in clear low resistance region
    if resistance < midpoint - margin:
        return 0, True
    # Check if in clear high resistance region
    elif resistance > midpoint + margin:
        return 1, True
    # Ambiguous region
    else:
        # Decide based on midpoint but mark as potentially invalid
        bit = 0 if resistance < midpoint else 1
        return bit, False


def verify_threshold_parameters(threshold_verification: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify threshold parameters are physically reasonable.
    
    Checks:
    - High threshold > Low threshold
    - Positive resistance values
    - Positive switching margin
    - TMR ratio consistency
    
    Args:
        threshold_verification: Threshold verification dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    low_r = threshold_verification.get("low_resistance_threshold", 0)
    high_r = threshold_verification.get("high_resistance_threshold", 0)
    margin = threshold_verification.get("switching_margin", 0)
    
    # Check positive values
    if low_r <= 0:
        errors.append(f"Low resistance threshold must be positive: {low_r}")
    if high_r <= 0:
        errors.append(f"High resistance threshold must be positive: {high_r}")
    
    # Check high > low
    if high_r <= low_r:
        errors.append(f"High threshold ({high_r}) must be greater than low threshold ({low_r})")
    
    # Check margin
    expected_margin = high_r - low_r
    if margin <= 0:
        errors.append(f"Switching margin must be positive: {margin}")
    elif abs(margin - expected_margin) > 0.01 * expected_margin:
        errors.append(f"Margin mismatch: expected ~{expected_margin:.2f}, got {margin:.2f}")
    
    # Check TMR if present
    tmr = threshold_verification.get("tmr_ratio")
    if tmr is not None:
        expected_tmr = (high_r - low_r) / low_r
        if abs(tmr - expected_tmr) > 0.01 * expected_tmr:
            errors.append(f"TMR ratio mismatch: expected ~{expected_tmr:.4f}, got {tmr:.4f}")
    
    return len(errors) == 0, errors


def verify_mram_write_read(packet: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify complete MRAM write/read operation.
    
    Checks:
    - Schema version
    - Threshold parameters
    - Write/read consistency
    - Resistance-to-bit decoding
    
    Args:
        packet: MRAM write/read receipt packet
        
    Returns:
        Tuple of (is_valid, verification_details)
    """
    errors = []
    
    # Check schema version
    if packet.get("schema_version") != "mram_write_read_v1":
        errors.append("Invalid schema version")
        return False, {"errors": errors}
    
    # Extract operations
    write_op = packet.get("write_operation", {})
    read_op = packet.get("read_operation", {})
    threshold_ver = packet.get("threshold_verification", {})
    
    # Verify threshold parameters
    thresholds_valid, threshold_errors = verify_threshold_parameters(threshold_ver)
    if not thresholds_valid:
        return False, {"errors": threshold_errors}
    
    # Get threshold values
    low_threshold = threshold_ver["low_resistance_threshold"]
    high_threshold = threshold_ver["high_resistance_threshold"]
    
    # Get write data
    written_bit = write_op.get("data_bit")
    if written_bit not in [0, 1]:
        errors.append(f"Invalid written bit: {written_bit}")
        return False, {"errors": errors}
    
    # Get read resistance
    resistance = read_op.get("resistance_state")
    if resistance is None or resistance <= 0:
        errors.append(f"Invalid resistance state: {resistance}")
        return False, {"errors": errors}
    
    # Decode resistance to bit
    decoded_bit, decode_valid = decode_resistance_to_bit(
        resistance, low_threshold, high_threshold
    )
    
    # Check if read operation has decoded bit
    read_decoded_bit = read_op.get("decoded_bit")
    
    # Verify write/read consistency
    write_read_consistent = (decoded_bit == written_bit)
    
    # Check if provided decoded bit matches our calculation
    if read_decoded_bit is not None and read_decoded_bit != decoded_bit:
        errors.append(f"Decoded bit mismatch: packet says {read_decoded_bit}, computed {decoded_bit}")
    
    # Prepare verification details
    details = {
        "written_bit": written_bit,
        "resistance_state": resistance,
        "decoded_bit": decoded_bit,
        "decode_valid": decode_valid,
        "write_read_consistent": write_read_consistent,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
        "switching_margin": threshold_ver["switching_margin"],
        "verification_passed": threshold_ver.get("verification_passed", write_read_consistent and decode_valid),
    }
    
    # Add TMR if present
    if "tmr_ratio" in threshold_ver:
        details["tmr_ratio"] = threshold_ver["tmr_ratio"]
    
    # Overall validation
    overall_valid = (
        len(errors) == 0 and
        write_read_consistent and
        decode_valid
    )
    
    if errors:
        details["errors"] = errors
    
    return overall_valid, details


def main():
    """Main entry point for verification script."""
    if len(sys.argv) < 2:
        print("Usage: verify_mram_write_read.py <receipt_file.json>", file=sys.stderr)
        return 1
    
    receipt_file = sys.argv[1]
    
    try:
        with open(receipt_file, 'r') as f:
            packet = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading receipt: {e}", file=sys.stderr)
        return 1
    
    # Verify MRAM operation
    is_valid, details = verify_mram_write_read(packet)
    
    if is_valid:
        print("MRAM WRITE/READ VERIFIED")
        print(f"  Written bit: {details['written_bit']}")
        print(f"  Resistance: {details['resistance_state']:.2f} Ω")
        print(f"  Decoded bit: {details['decoded_bit']}")
        print(f"  Switching margin: {details['switching_margin']:.2f} Ω")
        if "tmr_ratio" in details:
            print(f"  TMR ratio: {details['tmr_ratio']:.4f}")
        return 0
    else:
        print("MRAM WRITE/READ VERIFICATION FAILED", file=sys.stderr)
        if not details.get("write_read_consistent", True):
            print(f"  Write/read mismatch: wrote {details['written_bit']}, read {details['decoded_bit']}", file=sys.stderr)
        if not details.get("decode_valid", True):
            print(f"  Ambiguous resistance state: {details['resistance_state']:.2f} Ω", file=sys.stderr)
        if "errors" in details:
            for error in details["errors"]:
                print(f"  - {error}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
