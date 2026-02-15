#!/usr/bin/env python3
"""
MRAM Drift Detection Simulation Engine

Demonstrates REPEAT's capability to detect drift in MRAM hardware testing
that naive threshold logging would miss.

Usage:
    python3 simulate_mram_runs.py --mode pass --seed 42 --output receipts.jsonl
    python3 simulate_mram_runs.py --mode drift_fail --seed 42 --output receipts.jsonl
"""

import argparse
import hashlib
import json
import random
import sys
from typing import Dict, List, Any


def canonical_json(obj: Dict[str, Any]) -> bytes:
    """
    Compute canonical JSON bytes per REPEAT C14N v1 (JCS/RFC 8785).
    
    Rules:
    - UTF-8 encoding, no BOM
    - Keys sorted lexicographically
    - No insignificant whitespace
    - Numbers in shortest form
    """
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
        allow_nan=False
    ).encode('utf-8')


def sha256_c14n(obj: Dict[str, Any]) -> str:
    """Compute sha256 hash of canonical JSON."""
    canonical_bytes = canonical_json(obj)
    digest = hashlib.sha256(canonical_bytes).hexdigest()
    return f"sha256:{digest}"


def create_packet(device_id: str, num_runs: int, 
                  drift_tolerance_pct: float, baseline_window: int) -> Dict[str, Any]:
    """Create a test packet with device configuration and verifier parameters."""
    packet = {
        "schema": "repeat-spintronics-packet-v1",
        "device_baseline": {
            "device_id": device_id,
            "baseline_resistance_parallel_ohms": 1000.0,
            "baseline_resistance_antiparallel_ohms": 1500.0,
            "temperature_celsius": 25.0
        },
        "write_intent": {
            "target_state": "parallel",
            "write_current_ma": 5.0,
            "write_duration_ns": 100.0
        },
        "read_plan": {
            "num_runs": num_runs,
            "read_current_ma": 0.5,
            "measurement_delay_ns": 10.0
        },
        "verifier": {
            "threshold_resistance_ohms": 1250.0,
            "drift_tolerance_percent": drift_tolerance_pct,
            "baseline_window_size": baseline_window
        }
    }
    return packet


def simulate_resistance_measurement(run_id: int, mode: str, rng: random.Random) -> float:
    """
    Simulate a resistance measurement for MRAM in parallel state.
    
    Args:
        run_id: Current run number (1-indexed)
        mode: Simulation mode ('pass' or 'drift_fail')
        rng: Random number generator for deterministic behavior
    
    Returns:
        Measured resistance in ohms
    """
    base_resistance = 1000.0
    
    if mode == "pass":
        # Stable mode: small random noise around baseline
        noise = rng.gauss(0, 2.0)  # ~2 ohm standard deviation
        return base_resistance + noise
    
    elif mode == "drift_fail":
        # Drift failure mode: gradual upward drift
        # Still passes threshold (1250 ohms) but exceeds drift tolerance
        drift_factor = 0.003 * run_id  # 0.3% drift per run
        noise = rng.gauss(0, 1.0)  # smaller noise to show clear drift
        return base_resistance * (1.0 + drift_factor) + noise
    
    else:
        raise ValueError(f"Unknown mode: {mode}")


def compute_baseline_metrics(measurements: List[float], baseline_window: int) -> float:
    """Compute mean resistance from first N measurements (baseline window)."""
    baseline_samples = measurements[:baseline_window]
    return sum(baseline_samples) / len(baseline_samples)


def compute_drift_percentage(current_resistance: float, baseline_mean: float) -> float:
    """Compute drift percentage relative to baseline."""
    if baseline_mean == 0:
        return 0.0
    return 100.0 * (current_resistance - baseline_mean) / baseline_mean


def verify_run(run_id: int, measured_resistance: float, 
               baseline_mean: float, packet: Dict[str, Any]) -> tuple[bool, str]:
    """
    Verify a single run against REPEAT criteria.
    
    Returns:
        (pass_status, fail_reason)
    """
    threshold = packet["verifier"]["threshold_resistance_ohms"]
    drift_tolerance = packet["verifier"]["drift_tolerance_percent"]
    
    # Check threshold (naive approach)
    if measured_resistance > threshold:
        return False, "threshold_exceeded"
    
    # Check drift (REPEAT approach)
    if run_id > packet["verifier"]["baseline_window_size"]:
        drift_pct = compute_drift_percentage(measured_resistance, baseline_mean)
        if abs(drift_pct) > drift_tolerance:
            return False, "drift_detected"
    
    return True, ""


def create_receipt(packet: Dict[str, Any], packet_hash: str,
                   run_id: int, measured_resistance: float,
                   baseline_mean: float, drift_pct: float,
                   verdict_pass: bool, fail_reason: str) -> Dict[str, Any]:
    """Create a receipt for a single run."""
    # Build receipt without hashes first
    receipt_data = {
        "schema": "repeat-spintronics-receipt-v1",
        "packet_hash_sha256": packet_hash,
        "run_id": run_id,
        "measured_resistance_ohms": round(measured_resistance, 4),
        "verdict": {
            "pass": verdict_pass
        },
        "metrics": {
            "mean_resistance_ohms": round(baseline_mean, 4),
            "drift_pct": round(drift_pct, 4)
        }
    }
    
    # Add fail_reason only if failed
    if not verdict_pass:
        receipt_data["verdict"]["fail_reason"] = fail_reason
    
    # Compute evidence hash (receipt without receipt_hash_sha256)
    evidence_hash = sha256_c14n(receipt_data)
    receipt_data["evidence_hash_sha256"] = evidence_hash
    
    # Compute receipt hash (full receipt)
    receipt_hash = sha256_c14n(receipt_data)
    receipt_data["receipt_hash_sha256"] = receipt_hash
    
    return receipt_data


def run_simulation(mode: str, seed: int, output_file: str) -> None:
    """Run the full MRAM simulation."""
    # Initialize deterministic RNG
    rng = random.Random(seed)
    
    # Configuration
    device_id = "MRAM-A1B2C3D4"
    num_runs = 100
    baseline_window = 10
    drift_tolerance_pct = 5.0  # 5% drift tolerance
    
    # Create packet
    packet = create_packet(device_id, num_runs, drift_tolerance_pct, baseline_window)
    packet_hash = sha256_c14n(packet)
    
    # Storage
    measurements = []
    receipts = []
    pass_count = 0
    fail_count = 0
    
    # Run simulation
    for run_id in range(1, num_runs + 1):
        # Measure resistance
        measured_resistance = simulate_resistance_measurement(run_id, mode, rng)
        measurements.append(measured_resistance)
        
        # Compute metrics
        if run_id <= baseline_window:
            baseline_mean = sum(measurements) / len(measurements)
        else:
            baseline_mean = compute_baseline_metrics(measurements, baseline_window)
        
        drift_pct = compute_drift_percentage(measured_resistance, baseline_mean)
        
        # Verify
        verdict_pass, fail_reason = verify_run(run_id, measured_resistance, 
                                                baseline_mean, packet)
        
        # Create receipt
        receipt = create_receipt(packet, packet_hash, run_id, measured_resistance,
                                 baseline_mean, drift_pct, verdict_pass, fail_reason)
        receipts.append(receipt)
        
        # Update counts
        if verdict_pass:
            pass_count += 1
        else:
            fail_count += 1
    
    # Write receipts to JSONL file
    with open(output_file, 'w') as f:
        for receipt in receipts:
            f.write(json.dumps(receipt, sort_keys=True) + '\n')
    
    # Print summary
    print(f"Simulation complete: mode={mode}, seed={seed}")
    print(f"  Total runs: {num_runs}")
    print(f"  PASS: {pass_count}")
    print(f"  FAIL: {fail_count}")
    print(f"  Receipts written to: {output_file}")
    print(f"  Packet hash: {packet_hash}")
    
    # Show first failure if any
    for i, receipt in enumerate(receipts):
        if not receipt["verdict"]["pass"]:
            print(f"  First failure: run_id={receipt['run_id']}, "
                  f"reason={receipt['verdict']['fail_reason']}")
            break


def main():
    parser = argparse.ArgumentParser(
        description="MRAM drift detection simulation with REPEAT verification"
    )
    parser.add_argument(
        "--mode",
        choices=["pass", "drift_fail"],
        required=True,
        help="Simulation mode: 'pass' (stable) or 'drift_fail' (drift violation)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic simulation (default: 42)"
    )
    parser.add_argument(
        "--output",
        default="mram_receipts.jsonl",
        help="Output file for JSONL receipts (default: mram_receipts.jsonl)"
    )
    
    args = parser.parse_args()
    
    try:
        run_simulation(args.mode, args.seed, args.output)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
