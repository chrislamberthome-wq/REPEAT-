#!/usr/bin/env python3
"""
Initialization and build verification script for spintronics MRAM MVP.

This script performs deterministic initialization and validation with a PASS result.
"""

import sys
import json
from repeat_spintronics import (
    encode_to_magnetization,
    decode_from_magnetization,
    create_mram_packet,
    read_mram_packet,
    verify_packet_receipt,
)


def init_and_verify():
    """Initialize and verify the spintronics MRAM MVP system."""
    
    print("=" * 60)
    print("REPEAT Spintronics MRAM MVP - Initialization & Verification")
    print("=" * 60)
    print()
    
    # Test 1: Basic encoding/decoding
    print("[1/5] Testing magnetization texture encoding...")
    test_data = b"REPEAT_SPINTRONICS_MVP"
    textures = encode_to_magnetization(test_data)
    decoded = decode_from_magnetization(textures)
    
    if decoded == test_data:
        print("  ✓ Encoding/decoding verified")
    else:
        print("  ✗ Encoding/decoding failed")
        return False
    
    # Test 2: Packet creation
    print("[2/5] Testing MRAM packet creation...")
    packet = create_mram_packet(test_data, operation="write")
    
    required_fields = ["version", "packet_id", "operation", "timestamp", "data", "checksum"]
    if all(field in packet for field in required_fields):
        print(f"  ✓ Packet created with all required fields")
        print(f"    - Packet ID: {packet['packet_id']}")
        print(f"    - Textures: {len(packet['data']['textures'])}")
    else:
        print("  ✗ Packet creation failed")
        return False
    
    # Test 3: Packet reading
    print("[3/5] Testing MRAM packet reading...")
    read_data = read_mram_packet(packet)
    
    if read_data == test_data:
        print("  ✓ Packet read successfully")
        print(f"    - Decoded: {read_data.decode('utf-8')}")
    else:
        print("  ✗ Packet reading failed")
        return False
    
    # Test 4: Receipt verification
    print("[4/5] Testing verifier proof generation...")
    receipt = verify_packet_receipt(packet)
    
    if receipt["status"] == "success" and receipt["verifier_proof"]["verification_status"] == "verified":
        print("  ✓ Verifier proof generated and validated")
        print(f"    - Receipt ID: {receipt['receipt_id']}")
        print(f"    - Proof chain length: {len(receipt['verifier_proof']['proof_chain'])}")
        print(f"    - Verification: {receipt['verifier_proof']['verification_status']}")
    else:
        print("  ✗ Receipt verification failed")
        return False
    
    # Test 5: Schema validation (basic)
    print("[5/5] Testing schema compliance...")
    try:
        # Verify packet can be serialized
        packet_json = json.dumps(packet, indent=2)
        receipt_json = json.dumps(receipt, indent=2)
        
        # Verify can be deserialized
        packet_check = json.loads(packet_json)
        receipt_check = json.loads(receipt_json)
        
        print("  ✓ Packet and receipt are JSON-serializable")
        print(f"    - Packet size: {len(packet_json)} bytes")
        print(f"    - Receipt size: {len(receipt_json)} bytes")
    except Exception as e:
        print(f"  ✗ Schema validation failed: {e}")
        return False
    
    return True


def main():
    """Main entry point."""
    print()
    
    success = init_and_verify()
    
    print()
    print("=" * 60)
    if success:
        print("RESULT: PASS ✓")
        print("All tests passed. Spintronics MRAM MVP is operational.")
        exit_code = 0
    else:
        print("RESULT: FAIL ✗")
        print("Initialization failed. Check error messages above.")
        exit_code = 1
    
    print("=" * 60)
    print()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
