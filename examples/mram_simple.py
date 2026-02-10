#!/usr/bin/env python3
"""
Simple example showing REPEAT protocol for MRAM device.

This demonstrates encoding a binary bit, simulating MRAM measurement,
and running the complete REPEAT verification protocol.
"""

from repeat_hd import SpinReading, run_repeat_protocol
import json


def main():
    print("=" * 60)
    print("REPEAT Protocol Example: MRAM Bit Storage")
    print("=" * 60)
    
    # Encode binary 0
    print("\nEncoding binary 0...")
    reading_0 = SpinReading(
        resistance=1000.0,  # Low resistance = parallel alignment
        measured_theta=0.01  # Near north pole on Bloch sphere
    )
    
    packet_0 = run_repeat_protocol(
        binary=0,
        reading=reading_0,
        device_type="MRAM",
        pulse_amplitude=0.5,  # Tesla
        pulse_duration=10.0,  # nanoseconds
        temperature=300.0  # Kelvin
    )
    
    print(f"  Decoded binary: {packet_0.decoded_binary}")
    print(f"  Verification passed: {packet_0.receipt['all_verifications_passed']}")
    print(f"  Trace hash: {packet_0.trace_hash[:16]}...")
    
    # Encode binary 1
    print("\nEncoding binary 1...")
    reading_1 = SpinReading(
        resistance=2000.0,  # High resistance = antiparallel alignment
        measured_theta=3.13  # Near south pole on Bloch sphere
    )
    
    packet_1 = run_repeat_protocol(
        binary=1,
        reading=reading_1,
        device_type="MRAM",
        pulse_amplitude=0.5,
        pulse_duration=10.0,
        temperature=300.0
    )
    
    print(f"  Decoded binary: {packet_1.decoded_binary}")
    print(f"  Verification passed: {packet_1.receipt['all_verifications_passed']}")
    print(f"  Trace hash: {packet_1.trace_hash[:16]}...")
    
    # Export packet as JSON
    print("\nExporting trace packet to JSON...")
    packet_dict = packet_0.to_dict()
    
    # Save to file
    with open('/tmp/trace_packet_example.json', 'w') as f:
        json.dump(packet_dict, f, indent=2)
    
    print("  Saved to: /tmp/trace_packet_example.json")
    print(f"  Size: {len(json.dumps(packet_dict))} bytes")
    
    # Show verification details
    print("\nVerification Layers:")
    for v in packet_0.verifications:
        status = "PASS" if v.passed else "FAIL"
        print(f"  Layer {v.layer} ({v.layer_name}): {status}")
    
    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
