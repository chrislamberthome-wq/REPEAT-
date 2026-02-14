#!/usr/bin/env python3
"""
emit_receipt.py - Generate REPEAT receipts from trace files

This tool reads a protocol trace (JSONL format) and generates a tamper-evident
receipt with cryptographic hashes and metadata.

Usage:
    python tools/emit_receipt.py <trace_file> [--output <receipt_file>]
"""

import json
import hashlib
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List


VERIFIER_VERSION = "1.0.0"


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


def extract_protocol_info(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract protocol information from trace events."""
    protocol_id = None
    run_id = None
    verdict = "FAIL"  # Default to FAIL if not specified
    
    for event in events:
        if event.get("event_type") == "protocol_start":
            protocol_id = event.get("data", {}).get("protocol_id")
            
        if "run_id" in event:
            run_id = event["run_id"]
            
        if event.get("event_type") == "protocol_complete":
            verdict = event.get("data", {}).get("summary", {}).get("verdict", "FAIL")
    
    return {
        "protocol_id": protocol_id or "unknown",
        "run_id": run_id or "unknown",
        "verdict": verdict
    }


def compute_inputs_hash(events: List[Dict[str, Any]]) -> str:
    """Compute hash of protocol inputs."""
    # Extract inputs from protocol_start event
    for event in events:
        if event.get("event_type") == "protocol_start":
            inputs = {
                "protocol_id": event.get("data", {}).get("protocol_id"),
                "protocol_version": event.get("data", {}).get("protocol_version"),
                "num_samples": event.get("data", {}).get("num_samples")
            }
            return compute_canonical_hash(inputs)
    
    # Fallback: hash empty inputs
    return compute_canonical_hash({})


def compute_outputs_hash(events: List[Dict[str, Any]]) -> str:
    """Compute hash of protocol outputs."""
    # Extract outputs from protocol_complete event
    for event in reversed(events):
        if event.get("event_type") == "protocol_complete":
            outputs = event.get("data", {}).get("summary", {})
            return compute_canonical_hash(outputs)
    
    # Fallback: hash empty outputs
    return compute_canonical_hash({})


def generate_receipt(trace_path: str) -> Dict[str, Any]:
    """Generate a receipt from a trace file."""
    # Parse trace
    events = parse_trace(trace_path)
    if not events:
        raise ValueError("Trace file is empty or invalid")
    
    # Extract protocol info
    info = extract_protocol_info(events)
    
    # Compute hashes
    inputs_hash = compute_inputs_hash(events)
    outputs_hash = compute_outputs_hash(events)
    trace_hash = compute_file_hash(trace_path)
    
    # Generate receipt
    receipt = {
        "protocol_id": info["protocol_id"],
        "run_id": info["run_id"],
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "trace_hash": trace_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": info["verdict"],
        "verifier_version": VERIFIER_VERSION
    }
    
    return receipt


def main():
    parser = argparse.ArgumentParser(
        description="Generate a REPEAT receipt from a trace file"
    )
    parser.add_argument(
        "trace_file",
        help="Path to the trace file (JSONL format)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for receipt (default: <trace_file>.receipt.json)"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the receipt JSON"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.trace_file).exists():
        print(f"Error: Trace file not found: {args.trace_file}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output path
    if args.output is None:
        trace_path = Path(args.trace_file)
        # Replace .trace.jsonl with .receipt.json
        if trace_path.suffix == '.jsonl' and trace_path.stem.endswith('.trace'):
            output_path = trace_path.parent / (trace_path.stem.replace('.trace', '') + '.receipt.json')
        else:
            output_path = trace_path.with_suffix('.receipt.json')
        args.output = str(output_path)
    
    print(f"=== REPEAT Receipt Generator ===")
    print(f"Trace file: {args.trace_file}")
    print(f"Output: {args.output}")
    print()
    
    try:
        # Generate receipt
        receipt = generate_receipt(args.trace_file)
        
        # Write receipt
        with open(args.output, 'w') as f:
            if args.pretty:
                json.dump(receipt, f, indent=2)
                f.write('\n')
            else:
                json.dump(receipt, f)
                f.write('\n')
        
        print(f"Receipt generated successfully!")
        print()
        print(f"Protocol ID: {receipt['protocol_id']}")
        print(f"Run ID: {receipt['run_id']}")
        print(f"Verdict: {receipt['verdict']}")
        print(f"Trace hash: {receipt['trace_hash'][:16]}...")
        print()
        print(f"Next step: python tools/verify_receipt.py {args.output}")
        
    except Exception as e:
        print(f"Error generating receipt: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
