#!/usr/bin/env python3
"""Demonstration script for the 3D codec system."""

from repeat_hd import (
    encode_2d, decode_2d,
    encode_3d_seashell, decode_3d_seashell,
    encode_3d_solids, decode_3d_solids_rule_a, decode_3d_solids_rule_b,
    EPSILON
)


def demo_2d_codec():
    """Demonstrate the 2D codec."""
    print("=" * 60)
    print("2D CODEC DEMONSTRATION")
    print("=" * 60)
    
    for binary in [0, 1]:
        point = encode_2d(binary)
        decoded = decode_2d(point)
        print(f"\nBinary: {binary}")
        print(f"  Encoded to 2D point: ({point[0]:.6f}, {point[1]:.6f})")
        print(f"  Decoded back to: {decoded}")
        print(f"  ✓ Roundtrip successful" if decoded == binary else "  ✗ Roundtrip failed")


def demo_seashell_codec():
    """Demonstrate the seashell 3D codec."""
    print("\n" + "=" * 60)
    print("3D SEASHELL CODEC DEMONSTRATION")
    print("=" * 60)
    
    for binary in [0, 1]:
        point = encode_3d_seashell(binary)
        decoded = decode_3d_seashell(point)
        print(f"\nBinary: {binary}")
        print(f"  Encoded to 3D point: ({point[0]:.6f}, {point[1]:.6f}, {point[2]:.6f})")
        print(f"  Z-coordinate: {point[2]:.6f} ({'negative' if point[2] < 0 else 'positive'})")
        print(f"  Decoded back to: {decoded}")
        print(f"  ✓ Roundtrip successful" if decoded == binary else "  ✗ Roundtrip failed")


def demo_solids_codec():
    """Demonstrate the 5-solids 3D codec."""
    print("\n" + "=" * 60)
    print("3D 5-SOLIDS CODEC DEMONSTRATION")
    print("=" * 60)
    
    solid_names = ["Tetrahedron", "Cube", "Octahedron", "Dodecahedron", "Icosahedron"]
    
    for binary in [0, 1]:
        angles = encode_3d_solids(binary)
        decoded_a = decode_3d_solids_rule_a(angles)
        decoded_b = decode_3d_solids_rule_b(angles)
        
        print(f"\nBinary: {binary}")
        print("  Stopping angles (in radians):")
        
        votes = []
        cosines = []
        for i, (name, angle) in enumerate(zip(solid_names, angles)):
            import math
            cos_val = math.cos(angle)
            vote = 0 if cos_val >= 0 else 1
            votes.append(vote)
            cosines.append(cos_val)
            print(f"    {name:15s}: α = {angle:.6f}, cos(α) = {cos_val:+.6f}, vote = {vote}")
        
        cosine_sum = sum(cosines)
        majority_vote = 1 if sum(votes) > len(votes) / 2 else 0
        
        print(f"\n  Rule A (Majority Voting):")
        print(f"    Votes: {votes}")
        print(f"    Majority vote: {majority_vote}")
        print(f"    Decoded: {decoded_a}")
        print(f"    ✓ Correct" if decoded_a == binary else "    ✗ Incorrect")
        
        print(f"\n  Rule B (Sum Threshold):")
        print(f"    Sum of cosines: {cosine_sum:.6f}")
        print(f"    Decoded: {decoded_b} (sum {'≥' if cosine_sum >= 0 else '<'} 0)")
        print(f"    ✓ Correct" if decoded_b == binary else "    ✗ Incorrect")


def demo_tolerance_verification():
    """Demonstrate tolerance verification."""
    print("\n" + "=" * 60)
    print("TOLERANCE VERIFICATION DEMONSTRATION")
    print("=" * 60)
    print(f"\nTolerance threshold (ε): {EPSILON}")
    
    # Test 2D decoding with noise
    print("\n2D Decoding with noise:")
    import math
    
    # Perfect point for binary 1
    perfect = encode_2d(1)
    print(f"  Perfect point for b=1: ({perfect[0]:.6f}, {perfect[1]:.6f})")
    print(f"  Decodes to: {decode_2d(perfect)}")
    
    # Point with small noise (within tolerance)
    noisy = (perfect[0] + EPSILON * 0.5, perfect[1] + EPSILON * 0.2)
    result = decode_2d(noisy)
    print(f"\n  Noisy point (within ε): ({noisy[0]:.6f}, {noisy[1]:.6f})")
    print(f"  Decodes to: {result}")
    print(f"  ✓ Still valid" if result is not None else "  ✗ Verification failed")
    
    # Point with too much noise (outside tolerance)
    very_noisy = (perfect[0] + EPSILON * 3, perfect[1])
    result = decode_2d(very_noisy)
    print(f"\n  Very noisy point (outside ε): ({very_noisy[0]:.6f}, {very_noisy[1]:.6f})")
    print(f"  Decodes to: {result}")
    print(f"  ✓ Correctly rejected" if result is None else "  ✗ Should have failed")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("3D CODEC SYSTEM DEMONSTRATION")
    print("=" * 60)
    print("\nThis demonstration shows the encoding and decoding of binary")
    print("messages using geometric representations in 2D and 3D space.")
    
    demo_2d_codec()
    demo_seashell_codec()
    demo_solids_codec()
    demo_tolerance_verification()
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
