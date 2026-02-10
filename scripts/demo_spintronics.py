#!/usr/bin/env python3
"""Demonstration script for the spintronics REPEAT + Platoputer protocol.

This script demonstrates the key features of the spintronics module:
1. JSON canonicalization
2. Packet hashing
3. MRAM verification
4. Spin configuration verification
5. Pulse trace verification
"""

import json
from datetime import datetime
from spintronics import (
    canonicalize_json,
    hash_packet,
    compute_receipt_hash,
)
from spintronics.verifiers import (
    verify_mram_write_read,
    verify_spin_configuration,
    verify_trace_integrity,
)


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_canonicalization():
    """Demonstrate JSON canonicalization."""
    print_section("1. JSON Canonicalization")
    
    # Create a packet with unordered keys
    packet = {
        "timestamp": "2024-01-15T10:00:00Z",
        "id": "test-packet",
        "data": [1, 2, 3],
        "metadata": {"author": "demo", "version": 1}
    }
    
    print("Original packet (unordered keys):")
    print(json.dumps(packet, indent=2))
    
    # Canonicalize
    canonical = canonicalize_json(packet)
    print("\nCanonical form (sorted keys, no whitespace):")
    print(canonical)
    
    # Show hash
    packet_hash = hash_packet(packet)
    print(f"\nPacket hash: {packet_hash[:16]}...")


def demo_mram_verification():
    """Demonstrate MRAM write/read verification."""
    print_section("2. MRAM Write/Read Verification")
    
    # Load example MRAM receipt
    with open("spintronics/examples/example_mram_receipt.json") as f:
        receipt = json.load(f)
    
    print("Verifying MRAM receipt:")
    print(f"  Address: {receipt['write_operation']['address']}")
    print(f"  Written bit: {receipt['write_operation']['data_bit']}")
    print(f"  Resistance: {receipt['read_operation']['resistance_state']} Ω")
    
    # Verify
    is_valid, details = verify_mram_write_read(receipt)
    
    print(f"\nVerification result: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    print(f"  Decoded bit: {details['decoded_bit']}")
    print(f"  Write/read consistent: {details['write_read_consistent']}")
    print(f"  TMR ratio: {details.get('tmr_ratio', 'N/A')}")


def demo_spin_verification():
    """Demonstrate spin configuration verification."""
    print_section("3. Spin Configuration Verification")
    
    # Load example spin configuration
    with open("spintronics/examples/example_spin_configuration.json") as f:
        packet = json.load(f)
    
    config = packet["spin_configuration"]
    print("Spin lattice configuration:")
    print(f"  Size: {config['lattice_size']['x']}×{config['lattice_size']['y']}")
    print(f"  Spins: {config['spins']}")
    print(f"  Boundary: {packet['nearest_neighbors']['boundary_conditions']}")
    
    # Verify
    is_valid, errors = verify_spin_configuration(packet)
    
    print(f"\nConfiguration valid: {'✓ YES' if is_valid else '✗ NO'}")
    if errors:
        for error in errors:
            print(f"  Error: {error}")


def demo_trace_verification():
    """Demonstrate pulse trace verification."""
    print_section("4. Pulse Trace Verification")
    
    # Load example trace
    with open("spintronics/examples/example_pulse_trace.json") as f:
        packet = json.load(f)
    
    pulse_seq = packet["pulse_sequence"]
    print("Pulse trace:")
    print(f"  Pulse count: {len(pulse_seq)}")
    for i, pulse in enumerate(pulse_seq[:2]):  # Show first 2
        print(f"  Pulse {i}: {pulse['pulse_type']}, {pulse['amplitude']}V, {pulse['duration']}ns")
    if len(pulse_seq) > 2:
        print(f"  ... and {len(pulse_seq) - 2} more")
    
    # Verify
    is_valid, details = verify_trace_integrity(packet)
    
    print(f"\nTrace integrity: {'✓ VERIFIED' if is_valid else '✗ FAILED'}")
    print(f"  Checksum valid: {details['checksum_valid']}")
    print(f"  Total duration: {details['total_duration']} ns")


def demo_receipt_hashing():
    """Demonstrate receipt hash computation."""
    print_section("5. Receipt Hash Computation")
    
    # Create a simple write/read operation
    write_op = {
        "address": "0x1000",
        "data_bit": 1,
        "write_voltage": 1.8
    }
    
    read_op = {
        "resistance_state": 5000.0,
        "decoded_bit": 1
    }
    
    print("Computing receipt hash from operations:")
    print(f"  Write: address={write_op['address']}, bit={write_op['data_bit']}")
    print(f"  Read: R={read_op['resistance_state']}Ω, bit={read_op['decoded_bit']}")
    
    # Compute hash
    receipt_hash = compute_receipt_hash(write_op, read_op)
    
    print(f"\nReceipt hash: {receipt_hash[:32]}...")
    print(f"Full hash:    {receipt_hash}")


def main():
    """Run all demonstrations."""
    print("\n" + "="*70)
    print("  SPINTRONICS REPEAT + PLATOPUTER PROTOCOL DEMONSTRATION")
    print("="*70)
    
    demo_canonicalization()
    demo_mram_verification()
    demo_spin_verification()
    demo_trace_verification()
    demo_receipt_hashing()
    
    print("\n" + "="*70)
    print("  Demonstration complete!")
    print("="*70 + "\n")
    
    print("For more information, see:")
    print("  - spintronics/README.md")
    print("  - spintronics/mram_calibration.ipynb")
    print("  - spintronics/examples/README.md")
    print()


if __name__ == '__main__':
    main()
