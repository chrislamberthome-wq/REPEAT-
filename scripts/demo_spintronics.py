#!/usr/bin/env python3
"""Demonstration script for REPEAT + Platoputer spintronics applications."""

import json
from repeat_hd.spintronics import (
    SpinReading,
    run_repeat_protocol,
    encode_spin_symbol,
)


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_verification_results(verifications):
    """Print verification results in a formatted way."""
    print("\n  Verification Results:")
    for v in verifications:
        status = "✓ PASS" if v.passed else "✗ FAIL"
        print(f"    Layer {v.layer} - {v.layer_name}: {status}")
        print(f"      {v.message}")


def demo_mram_switching():
    """Demonstrate MRAM bit switching with REPEAT protocol."""
    print_header("MRAM BIT SWITCHING SCENARIO")
    
    print("\n  MRAM uses tunnel magnetoresistance (TMR) to store bits.")
    print("  - Parallel alignment = Low resistance = Binary 0")
    print("  - Antiparallel alignment = High resistance = Binary 1")
    
    for binary in [0, 1]:
        print(f"\n  Encoding binary {binary}:")
        
        # Simulate MRAM resistance measurement
        resistance = 1000.0 if binary == 0 else 2000.0
        measured_theta = 0.05 if binary == 0 else 3.10
        
        reading = SpinReading(
            resistance=resistance,
            measured_theta=measured_theta
        )
        
        # Run REPEAT protocol
        packet = run_repeat_protocol(
            binary=binary,
            reading=reading,
            device_type="MRAM",
            pulse_amplitude=0.5,
            pulse_duration=10.0,
            pulse_geometry="perpendicular",
            temperature=300.0
        )
        
        print(f"    Symbol: theta = {packet.experiment.symbol.theta:.3f} rad")
        print(f"    Measurement: R = {resistance:.0f} Ω, theta = {measured_theta:.3f} rad")
        print(f"    Decoded: {packet.decoded_binary}")
        print_verification_results(packet.verifications)
        print(f"    Trace hash: {packet.trace_hash[:16]}...")
        print(f"    All verifications passed: {packet.receipt['all_verifications_passed']}")


def demo_domain_wall_racetrack():
    """Demonstrate domain-wall racetrack memory."""
    print_header("DOMAIN-WALL RACETRACK MEMORY SCENARIO")
    
    print("\n  Racetrack memory stores bits as domain wall positions.")
    print("  - Current pulses move domain walls along a nanowire track")
    print("  - Position < threshold = Binary 0")
    print("  - Position ≥ threshold = Binary 1")
    
    positions = [0.2, 0.8]  # Low and high positions
    binaries = [0, 1]
    
    for binary, position in zip(binaries, positions):
        print(f"\n  Encoding binary {binary}:")
        
        reading = SpinReading(
            position=position,
            measured_theta=0.1 if binary == 0 else 3.0
        )
        
        packet = run_repeat_protocol(
            binary=binary,
            reading=reading,
            device_type="racetrack",
            pulse_amplitude=0.7,
            pulse_duration=50.0,
            pulse_geometry="in-plane",
            temperature=300.0
        )
        
        print(f"    Symbol: theta = {packet.experiment.symbol.theta:.3f} rad")
        print(f"    Measurement: position = {position:.2f} μm")
        print(f"    Decoded: {packet.decoded_binary}")
        print_verification_results(packet.verifications)
        print(f"    All verifications passed: {packet.receipt['all_verifications_passed']}")


def demo_skyrmion_stability():
    """Demonstrate skyrmion-based memory with topological protection."""
    print_header("SKYRMION STABILITY SCENARIO")
    
    print("\n  Skyrmions are topologically protected spin textures.")
    print("  - Positive topological charge = Stable skyrmion = Binary 1")
    print("  - Zero/negative charge = Unstable/absent = Binary 0")
    
    charges = [0, 1]
    binaries = [0, 1]
    
    for binary, charge in zip(binaries, charges):
        print(f"\n  Encoding binary {binary}:")
        
        reading = SpinReading(
            topological_charge=charge,
            measured_theta=0.2 if binary == 0 else 2.9
        )
        
        packet = run_repeat_protocol(
            binary=binary,
            reading=reading,
            device_type="skyrmion",
            pulse_amplitude=0.3,
            pulse_duration=5.0,
            pulse_geometry="perpendicular",
            temperature=4.0  # Low temperature for skyrmion stability
        )
        
        print(f"    Symbol: theta = {packet.experiment.symbol.theta:.3f} rad")
        print(f"    Measurement: Q = {charge} (topological charge)")
        print(f"    Decoded: {packet.decoded_binary}")
        print_verification_results(packet.verifications)
        print(f"    All verifications passed: {packet.receipt['all_verifications_passed']}")


def demo_magnonic_interference():
    """Demonstrate magnonic phase-coherent computation."""
    print_header("MAGNONIC PHASE-COHERENT COMPUTATION SCENARIO")
    
    print("\n  Magnonics uses spin waves for computation.")
    print("  - Phase near 0 = Constructive interference = Binary 0")
    print("  - Phase near π = Destructive interference = Binary 1")
    
    phases = [0.3, 2.8]  # Small and large phase
    binaries = [0, 1]
    
    for binary, phase in zip(binaries, phases):
        print(f"\n  Encoding binary {binary}:")
        
        reading = SpinReading(
            phase=phase,
            measured_theta=0.15 if binary == 0 else 2.95
        )
        
        packet = run_repeat_protocol(
            binary=binary,
            reading=reading,
            device_type="magnonic",
            pulse_amplitude=0.4,
            pulse_duration=15.0,
            pulse_geometry="rotating",
            temperature=300.0
        )
        
        print(f"    Symbol: theta = {packet.experiment.symbol.theta:.3f} rad")
        print(f"    Measurement: φ = {phase:.2f} rad")
        print(f"    Decoded: {packet.decoded_binary}")
        print_verification_results(packet.verifications)
        print(f"    All verifications passed: {packet.receipt['all_verifications_passed']}")


def demo_platonic_codebook():
    """Demonstrate the Platonic solids codebook."""
    print_header("PLATONIC SOLIDS CODEBOOK")
    
    print("\n  The codebook uses 5 Platonic solids to encode spin textures:")
    print("    - Tetrahedron (T)")
    print("    - Cube (C)")
    print("    - Octahedron (O)")
    print("    - Dodecahedron (D)")
    print("    - Icosahedron (I)")
    
    solid_names = ["Tetrahedron", "Cube", "Octahedron", "Dodecahedron", "Icosahedron"]
    
    for binary in [0, 1]:
        print(f"\n  Binary {binary} encoding:")
        symbol = encode_spin_symbol(binary)
        
        print(f"    Bloch sphere: theta = {symbol.theta:.3f} rad, phi = {symbol.phi:.3f} rad")
        print(f"    Platonic angles:")
        
        for name, angle in zip(solid_names, symbol.platonic_angles):
            import math
            cos_val = math.cos(angle)
            vote = 0 if cos_val >= 0 else 1
            print(f"      {name:15s}: α = {angle:.4f} rad, cos(α) = {cos_val:+.4f}, vote = {vote}")
        
        # Calculate majority vote
        import math
        votes = [0 if math.cos(a) >= 0 else 1 for a in symbol.platonic_angles]
        majority = 1 if sum(votes) > len(votes) / 2 else 0
        print(f"    Majority vote: {majority} (matches encoded: {majority == binary})")


def demo_trace_packet_export():
    """Demonstrate exporting trace packet as JSON."""
    print_header("TRACE PACKET EXPORT (JSON)")
    
    print("\n  REPEAT protocol generates auditable trace packets.")
    print("  These can be exported as JSON for external verification.")
    
    # Create a sample trace packet
    reading = SpinReading(resistance=1000.0, measured_theta=0.02)
    packet = run_repeat_protocol(
        binary=0,
        reading=reading,
        device_type="MRAM",
        pulse_amplitude=0.5,
        pulse_duration=10.0
    )
    
    # Export to JSON
    packet_dict = packet.to_dict()
    json_output = json.dumps(packet_dict, indent=2)
    
    print("\n  Sample trace packet (first 50 lines):")
    lines = json_output.split('\n')
    for line in lines[:50]:
        print(f"    {line}")
    
    if len(lines) > 50:
        print(f"    ... ({len(lines) - 50} more lines)")
    
    print(f"\n  Total size: {len(json_output)} bytes")
    print(f"  Trace hash: {packet.trace_hash}")
    print(f"  Protocol version: {packet.receipt['protocol_version']}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  REPEAT + PLATOPUTER SPINTRONICS APPLICATIONS")
    print("  Demonstration of Encode, Decode, Verify, and Repeat Protocol")
    print("=" * 70)
    
    demo_platonic_codebook()
    demo_mram_switching()
    demo_domain_wall_racetrack()
    demo_skyrmion_stability()
    demo_magnonic_interference()
    demo_trace_packet_export()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n  Key Features Demonstrated:")
    print("    ✓ Platonic solids codebook for spin textures")
    print("    ✓ REPEAT protocol: Encode → Decode → Verify → Repeat")
    print("    ✓ Three-layer verification system")
    print("    ✓ Four adoption scenarios: MRAM, Racetrack, Skyrmion, Magnonic")
    print("    ✓ Auditable trace packets with cryptographic hashes")
    print("    ✓ JSON export for cross-lab verification")
    print("\n")


if __name__ == "__main__":
    main()
