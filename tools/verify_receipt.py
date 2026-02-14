#!/usr/bin/env python3
"""
verify_receipt.py - Verify REPEAT receipts

This tool verifies the integrity and validity of a REPEAT receipt by:
1. Re-computing hashes from the trace file
2. Checking that hashes match the receipt
3. Validating the receipt format
4. Emitting a clear PASS or FAIL verdict

Usage:
    python tools/verify_receipt.py <receipt_file>
"""

import json
import hashlib
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple


def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_canonical_hash(data: Any) -> str:
    """Compute SHA-256 hash of canonicalized JSON data."""
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode()).hexdigest()


def parse_trace(trace_path: str) -> List[Dict[str, Any]]:
    """Parse JSONL trace file."""
    events = []
    with open(trace_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError as e:
                print(f"Warning: Skipping invalid JSON at line {line_num}: {e}", file=sys.stderr)
    return events


def compute_inputs_hash(events: List[Dict[str, Any]]) -> str:
    """Compute hash of protocol inputs."""
    for event in events:
        if event.get("event_type") == "protocol_start":
            inputs = {
                "protocol_id": event.get("data", {}).get("protocol_id"),
                "protocol_version": event.get("data", {}).get("protocol_version"),
                "num_samples": event.get("data", {}).get("num_samples")
            }
            return compute_canonical_hash(inputs)
    return compute_canonical_hash({})


def compute_outputs_hash(events: List[Dict[str, Any]]) -> str:
    """Compute hash of protocol outputs."""
    for event in reversed(events):
        if event.get("event_type") == "protocol_complete":
            outputs = event.get("data", {}).get("summary", {})
            return compute_canonical_hash(outputs)
    return compute_canonical_hash({})


def load_receipt(receipt_path: str) -> Dict[str, Any]:
    """Load receipt from file."""
    with open(receipt_path, 'r') as f:
        return json.load(f)


def find_trace_file(receipt_path: str) -> str:
    """Find the trace file corresponding to a receipt."""
    receipt_path_obj = Path(receipt_path)
    
    # Try standard naming convention
    if receipt_path_obj.stem.endswith('.receipt'):
        trace_name = receipt_path_obj.stem.replace('.receipt', '.trace.jsonl')
        trace_path = receipt_path_obj.parent / trace_name
        if trace_path.exists():
            return str(trace_path)
    
    # Try replacing .receipt.json with .trace.jsonl
    trace_path = receipt_path_obj.parent / receipt_path_obj.name.replace('.receipt.json', '.trace.jsonl')
    if trace_path.exists():
        return str(trace_path)
    
    # Look for any .trace.jsonl in the same directory
    for trace_file in receipt_path_obj.parent.glob('*.trace.jsonl'):
        return str(trace_file)
    
    raise FileNotFoundError(f"Could not find trace file for receipt: {receipt_path}")


def verify_receipt(receipt_path: str) -> Tuple[bool, List[str]]:
    """
    Verify a receipt.
    
    Returns:
        (passed, reasons): Tuple of bool and list of strings
    """
    reasons = []
    passed = True
    
    # Load receipt
    try:
        receipt = load_receipt(receipt_path)
    except Exception as e:
        return False, [f"Failed to load receipt: {e}"]
    
    # Validate required fields
    required_fields = [
        "protocol_id", "run_id", "inputs_hash", "outputs_hash",
        "trace_hash", "timestamp", "verdict", "verifier_version"
    ]
    
    for field in required_fields:
        if field not in receipt:
            passed = False
            reasons.append(f"Missing required field: {field}")
    
    if not passed:
        return passed, reasons
    
    # Find trace file
    try:
        trace_path = find_trace_file(receipt_path)
    except FileNotFoundError as e:
        return False, [str(e)]
    
    # Parse trace
    try:
        events = parse_trace(trace_path)
        if not events:
            return False, ["Trace file is empty"]
    except Exception as e:
        return False, [f"Failed to parse trace: {e}"]
    
    # Verify trace hash
    computed_trace_hash = compute_file_hash(trace_path)
    if computed_trace_hash != receipt["trace_hash"]:
        passed = False
        reasons.append(
            f"Trace hash mismatch: "
            f"expected {receipt['trace_hash'][:16]}..., "
            f"got {computed_trace_hash[:16]}..."
        )
    else:
        reasons.append("✓ Trace hash verified")
    
    # Verify inputs hash
    computed_inputs_hash = compute_inputs_hash(events)
    if computed_inputs_hash != receipt["inputs_hash"]:
        passed = False
        reasons.append(
            f"Inputs hash mismatch: "
            f"expected {receipt['inputs_hash'][:16]}..., "
            f"got {computed_inputs_hash[:16]}..."
        )
    else:
        reasons.append("✓ Inputs hash verified")
    
    # Verify outputs hash
    computed_outputs_hash = compute_outputs_hash(events)
    if computed_outputs_hash != receipt["outputs_hash"]:
        passed = False
        reasons.append(
            f"Outputs hash mismatch: "
            f"expected {receipt['outputs_hash'][:16]}..., "
            f"got {computed_outputs_hash[:16]}..."
        )
    else:
        reasons.append("✓ Outputs hash verified")
    
    # Check verdict
    if receipt["verdict"] not in ["PASS", "FAIL"]:
        passed = False
        reasons.append(f"Invalid verdict: {receipt['verdict']} (must be PASS or FAIL)")
    else:
        reasons.append(f"✓ Verdict is valid: {receipt['verdict']}")
    
    return passed, reasons


def main():
    parser = argparse.ArgumentParser(
        description="Verify a REPEAT receipt"
    )
    parser.add_argument(
        "receipt_file",
        help="Path to the receipt file (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed verification steps"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.receipt_file).exists():
        print(f"Error: Receipt file not found: {args.receipt_file}", file=sys.stderr)
        sys.exit(1)
    
    print(f"=== REPEAT Receipt Verifier ===")
    print(f"Receipt: {args.receipt_file}")
    print()
    
    # Verify receipt
    passed, reasons = verify_receipt(args.receipt_file)
    
    # Print results
    if args.verbose or not passed:
        for reason in reasons:
            print(reason)
        print()
    
    # Print verdict
    if passed:
        print("VERDICT: PASS")
        print("All integrity checks passed.")
        sys.exit(0)
    else:
        print("VERDICT: FAIL")
        print("Receipt verification failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
