#!/usr/bin/env python3
"""
Demonstration of the REPEAT Spintronics MRAM MVP system.

This script demonstrates the complete workflow of encoding data to magnetization
textures, creating MRAM packets, and verifying operations with SHA-based proofs.
"""

import json
from repeat_spintronics import (
    encode_to_magnetization,
    decode_from_magnetization,
    create_mram_packet,
    read_mram_packet,
    verify_packet_receipt,
)
from repeat_spintronics.encoder import get_tetrahedron_state


def print_section(title):
    """Print a section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def demo_encoding():
    """Demonstrate magnetization texture encoding."""
    print_section("1. Magnetization Texture Encoding")
    
    data = b"MRAM"
    print(f"Original data: {data}")
    print(f"Byte representation: {data.hex()}")
    print()
    
    # Encode to magnetization textures
    textures = encode_to_magnetization(data)
    print(f"Generated {len(textures)} magnetization textures")
    print(f"Each texture is a 5-angle tuple from Platonic solids:")
    print(f"  (α_T, α_C, α_O, α_D, α_I)")
    print()
    
    # Show first few textures
    print("First 3 textures:")
    for i, texture in enumerate(textures[:3]):
        tetra_state = get_tetrahedron_state(texture)
        print(f"  Texture {i}: α_T={texture[0]:.4f}, α_C={texture[1]:.4f}, "
              f"α_O={texture[2]:.4f}, α_D={texture[3]:.4f}, α_I={texture[4]:.4f}")
        print(f"    → Tetrahedron state: {tetra_state}")
    print("  ...")
    print()
    
    # Decode back
    decoded = decode_from_magnetization(textures)
    print(f"Decoded data: {decoded}")
    print(f"Match: {decoded == data} ✓")


def demo_packetization():
    """Demonstrate MRAM packet creation and reading."""
    print_section("2. MRAM Packet Creation and Reading")
    
    data = b"Spintronics MVP"
    print(f"Data to packetize: {data.decode('utf-8')}")
    print()
    
    # Create packet
    packet = create_mram_packet(data, operation="write")
    print("Created MRAM packet:")
    print(f"  Packet ID: {packet['packet_id']}")
    print(f"  Operation: {packet['operation']}")
    print(f"  Timestamp: {packet['timestamp']}")
    print(f"  Textures: {len(packet['data']['textures'])}")
    print(f"  Byte count: {packet['data']['metadata']['byte_count']}")
    print(f"  Encoding method: {packet['data']['metadata']['encoding_method']}")
    print(f"  Checksum: {packet['checksum'][:16]}...")
    print()
    
    # Serialize to JSON
    packet_json = json.dumps(packet, indent=2)
    print(f"Packet JSON size: {len(packet_json)} bytes")
    print()
    
    # Read packet
    decoded = read_mram_packet(packet)
    print(f"Read from packet: {decoded.decode('utf-8')}")
    print(f"Match: {decoded == data} ✓")


def demo_verification():
    """Demonstrate verifier proof generation."""
    print_section("3. SHA-Based Verifier Proofs")
    
    data = b"Verified"
    print(f"Data to verify: {data.decode('utf-8')}")
    print()
    
    # Create packet
    packet = create_mram_packet(data)
    print(f"Created packet {packet['packet_id'][:8]}...")
    print()
    
    # Generate receipt with verifier proof
    receipt = verify_packet_receipt(packet)
    print("Generated receipt:")
    print(f"  Receipt ID: {receipt['receipt_id']}")
    print(f"  Status: {receipt['status']}")
    print(f"  Verification: {receipt['verifier_proof']['verification_status']}")
    print()
    
    # Show proof chain
    proof = receipt['verifier_proof']
    print("SHA-256 Proof Chain:")
    print(f"  1. Packet hash:  {proof['packet_hash'][:32]}...")
    print(f"  2. Data hash:    {proof['data_hash'][:32]}...")
    for i, hash_val in enumerate(proof['proof_chain'], 1):
        print(f"  {i+2}. Chain step {i}: {hash_val[:32]}...")
    print()
    
    print(f"Decoded bytes: {receipt['result']['decoded_bytes']}")
    print(f"Status: {receipt['status']} ✓")


def demo_workflow():
    """Demonstrate complete workflow."""
    print_section("4. Complete Workflow")
    
    # Step 1: Encode
    original_data = b"REPEAT Platoputer Integration"
    print(f"Step 1: Original data")
    print(f"  → {original_data.decode('utf-8')}")
    print()
    
    # Step 2: Create packet
    packet = create_mram_packet(original_data, operation="write")
    print(f"Step 2: MRAM packet created")
    print(f"  → ID: {packet['packet_id']}")
    print(f"  → {len(packet['data']['textures'])} magnetization textures")
    print()
    
    # Step 3: Read packet
    decoded_data = read_mram_packet(packet)
    print(f"Step 3: Read packet")
    print(f"  → Decoded: {decoded_data.decode('utf-8')}")
    print()
    
    # Step 4: Verify with receipt
    receipt = verify_packet_receipt(packet, decoded_data)
    print(f"Step 4: Verify operation")
    print(f"  → Receipt ID: {receipt['receipt_id']}")
    print(f"  → Status: {receipt['status']}")
    print(f"  → Verification: {receipt['verifier_proof']['verification_status']}")
    print(f"  → Proof chain: {len(receipt['verifier_proof']['proof_chain'])} steps")
    print()
    
    # Verify end-to-end
    if decoded_data == original_data and receipt['status'] == 'success':
        print("✓ Complete workflow verified successfully!")
    else:
        print("✗ Workflow verification failed")


def demo_determinism():
    """Demonstrate deterministic encoding."""
    print_section("5. Deterministic Encoding")
    
    data = b"Deterministic"
    print(f"Data: {data.decode('utf-8')}")
    print()
    
    # Encode multiple times
    print("Encoding the same data 3 times...")
    textures1 = encode_to_magnetization(data)
    textures2 = encode_to_magnetization(data)
    textures3 = encode_to_magnetization(data)
    
    # Compare
    match12 = textures1 == textures2
    match23 = textures2 == textures3
    match13 = textures1 == textures3
    
    print(f"  Encoding 1 == Encoding 2: {match12}")
    print(f"  Encoding 2 == Encoding 3: {match23}")
    print(f"  Encoding 1 == Encoding 3: {match13}")
    print()
    
    if match12 and match23 and match13:
        print("✓ Encoding is deterministic")
    else:
        print("✗ Encoding is not deterministic")


def main():
    """Run all demonstrations."""
    print()
    print("*" * 70)
    print("  REPEAT Spintronics MRAM MVP - Demonstration")
    print("*" * 70)
    
    demo_encoding()
    demo_packetization()
    demo_verification()
    demo_workflow()
    demo_determinism()
    
    print()
    print("*" * 70)
    print("  Demonstration Complete")
    print("*" * 70)
    print()


if __name__ == "__main__":
    main()
