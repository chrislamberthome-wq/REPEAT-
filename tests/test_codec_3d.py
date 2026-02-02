"""Tests for the 3D codec system."""

import pytest
import math
from repeat_hd.codec_3d import (
    wrap_angle,
    encode_2d,
    decode_2d,
    encode_3d_seashell,
    decode_3d_seashell,
    encode_3d_solids,
    decode_3d_solids_rule_a,
    decode_3d_solids_rule_b,
    verify_tolerance,
    EPSILON,
    DEFAULT_RADIUS,
)


class TestWrapAngle:
    """Tests for wrap_angle helper function."""
    
    def test_wrap_angle_zero(self):
        """Test wrapping angle 0."""
        assert wrap_angle(0.0) == 0.0
    
    def test_wrap_angle_pi(self):
        """Test wrapping angle π."""
        result = wrap_angle(math.pi)
        assert abs(result - math.pi) < 1e-10
    
    def test_wrap_angle_negative_pi(self):
        """Test wrapping angle -π."""
        result = wrap_angle(-math.pi)
        assert abs(result - (-math.pi)) < 1e-10 or abs(result - math.pi) < 1e-10
    
    def test_wrap_angle_greater_than_pi(self):
        """Test wrapping angle > π."""
        result = wrap_angle(3 * math.pi / 2)
        expected = -math.pi / 2
        assert abs(result - expected) < 1e-10
    
    def test_wrap_angle_less_than_negative_pi(self):
        """Test wrapping angle < -π."""
        result = wrap_angle(-3 * math.pi / 2)
        expected = math.pi / 2
        assert abs(result - expected) < 1e-10
    
    def test_wrap_angle_two_pi(self):
        """Test wrapping angle 2π."""
        result = wrap_angle(2 * math.pi)
        assert abs(result) < 1e-10  # Should wrap to 0


class TestEncode2D:
    """Tests for encode_2d function."""
    
    def test_encode_2d_binary_0(self):
        """Test encoding binary 0 to 2D point."""
        x, y = encode_2d(0)
        # For b=0: θ=0, so point is (R, 0)
        assert abs(x - DEFAULT_RADIUS) < 1e-10
        assert abs(y - 0.0) < 1e-10
    
    def test_encode_2d_binary_1(self):
        """Test encoding binary 1 to 2D point."""
        x, y = encode_2d(1)
        # For b=1: θ=π, so point is (-R, 0)
        assert abs(x - (-DEFAULT_RADIUS)) < 1e-10
        assert abs(y - 0.0) < 1e-10
    
    def test_encode_2d_custom_radius(self):
        """Test encoding with custom radius."""
        radius = 2.5
        x, y = encode_2d(0, radius=radius)
        assert abs(x - radius) < 1e-10
        assert abs(y - 0.0) < 1e-10
    
    def test_encode_2d_invalid_input(self):
        """Test encoding with invalid binary input."""
        with pytest.raises(ValueError):
            encode_2d(2)
        with pytest.raises(ValueError):
            encode_2d(-1)


class TestDecode2D:
    """Tests for decode_2d function."""
    
    def test_decode_2d_binary_0(self):
        """Test decoding 2D point to binary 0."""
        point = encode_2d(0)
        result = decode_2d(point)
        assert result == 0
    
    def test_decode_2d_binary_1(self):
        """Test decoding 2D point to binary 1."""
        point = encode_2d(1)
        result = decode_2d(point)
        assert result == 1
    
    def test_decode_2d_roundtrip(self):
        """Test encode-decode roundtrip for both values."""
        for b in [0, 1]:
            point = encode_2d(b)
            decoded = decode_2d(point)
            assert decoded == b
    
    def test_decode_2d_with_tolerance(self):
        """Test decoding with slight noise within tolerance."""
        # Point close to (1, 0) for b=0
        point = (1.0 + EPSILON * 0.5, 0.01)
        result = decode_2d(point)
        assert result == 0
    
    def test_decode_2d_outside_tolerance(self):
        """Test decoding fails when point is outside tolerance."""
        # Point far from expected circle
        point = (2.0, 0.0)
        result = decode_2d(point)
        assert result is None
    
    def test_decode_2d_wrong_angle(self):
        """Test decoding fails for wrong angle."""
        # Point at angle π/2 (neither 0 nor π)
        point = (0.0, 1.0)
        result = decode_2d(point)
        assert result is None


class TestEncode3DSeashell:
    """Tests for encode_3d_seashell function."""
    
    def test_encode_seashell_binary_0(self):
        """Test encoding binary 0 with seashell curve."""
        x, y, z = encode_3d_seashell(0)
        # For b=0, z should be negative
        assert z < 0
    
    def test_encode_seashell_binary_1(self):
        """Test encoding binary 1 with seashell curve."""
        x, y, z = encode_3d_seashell(1)
        # For b=1, z should be positive
        assert z > 0
    
    def test_encode_seashell_custom_parameters(self):
        """Test encoding with custom parameters."""
        r0, phi, t = 2.0, 1.5, 2.0
        x, y, z = encode_3d_seashell(0, r0=r0, phi=phi, t=t)
        
        # Verify r = r0 * phi^t
        expected_r = r0 * (phi ** t)
        actual_r = math.sqrt(x*x + y*y)
        assert abs(actual_r - expected_r) < 1e-10
        
        # Verify z = -r for b=0
        assert abs(z - (-expected_r)) < 1e-10
    
    def test_encode_seashell_invalid_input(self):
        """Test encoding with invalid binary input."""
        with pytest.raises(ValueError):
            encode_3d_seashell(2)


class TestDecode3DSeashell:
    """Tests for decode_3d_seashell function."""
    
    def test_decode_seashell_binary_0(self):
        """Test decoding seashell point to binary 0."""
        point = encode_3d_seashell(0)
        result = decode_3d_seashell(point)
        assert result == 0
    
    def test_decode_seashell_binary_1(self):
        """Test decoding seashell point to binary 1."""
        point = encode_3d_seashell(1)
        result = decode_3d_seashell(point)
        assert result == 1
    
    def test_decode_seashell_roundtrip(self):
        """Test encode-decode roundtrip for seashell mode."""
        for b in [0, 1]:
            point = encode_3d_seashell(b)
            decoded = decode_3d_seashell(point)
            assert decoded == b
    
    def test_decode_seashell_negative_z(self):
        """Test decoding point with negative z."""
        point = (1.0, 2.0, -3.0)
        assert decode_3d_seashell(point) == 0
    
    def test_decode_seashell_positive_z(self):
        """Test decoding point with positive z."""
        point = (1.0, 2.0, 3.0)
        assert decode_3d_seashell(point) == 1
    
    def test_decode_seashell_zero_z(self):
        """Test decoding point with z=0 (edge case)."""
        point = (1.0, 2.0, 0.0)
        # z >= 0, so should decode to 1
        assert decode_3d_seashell(point) == 1


class TestEncode3DSolids:
    """Tests for encode_3d_solids function."""
    
    def test_encode_solids_binary_0(self):
        """Test encoding binary 0 with 5-solids frame."""
        angles = encode_3d_solids(0)
        assert len(angles) == 5
        
        # For b=0, majority of cos(alpha) should be >= 0
        positive_count = sum(1 for alpha in angles if math.cos(alpha) >= 0)
        assert positive_count > 2  # Majority
    
    def test_encode_solids_binary_1(self):
        """Test encoding binary 1 with 5-solids frame."""
        angles = encode_3d_solids(1)
        assert len(angles) == 5
        
        # For b=1, majority of cos(alpha) should be < 0
        negative_count = sum(1 for alpha in angles if math.cos(alpha) < 0)
        assert negative_count > 2  # Majority
    
    def test_encode_solids_invalid_input(self):
        """Test encoding with invalid binary input."""
        with pytest.raises(ValueError):
            encode_3d_solids(3)


class TestDecode3DSolidsRuleA:
    """Tests for decode_3d_solids_rule_a function."""
    
    def test_decode_solids_rule_a_binary_0(self):
        """Test decoding with Rule A for binary 0."""
        angles = encode_3d_solids(0)
        result = decode_3d_solids_rule_a(angles)
        assert result == 0
    
    def test_decode_solids_rule_a_binary_1(self):
        """Test decoding with Rule A for binary 1."""
        angles = encode_3d_solids(1)
        result = decode_3d_solids_rule_a(angles)
        assert result == 1
    
    def test_decode_solids_rule_a_roundtrip(self):
        """Test encode-decode roundtrip with Rule A."""
        for b in [0, 1]:
            angles = encode_3d_solids(b)
            decoded = decode_3d_solids_rule_a(angles)
            assert decoded == b
    
    def test_decode_solids_rule_a_custom_angles(self):
        """Test Rule A with custom angles."""
        # 3 positive cosines, 2 negative → majority vote 0
        angles = (0.0, math.pi/4, math.pi/3, 3*math.pi/4, math.pi)
        result = decode_3d_solids_rule_a(angles)
        assert result == 0


class TestDecode3DSolidsRuleB:
    """Tests for decode_3d_solids_rule_b function."""
    
    def test_decode_solids_rule_b_binary_0(self):
        """Test decoding with Rule B for binary 0."""
        angles = encode_3d_solids(0)
        result = decode_3d_solids_rule_b(angles)
        assert result == 0
    
    def test_decode_solids_rule_b_binary_1(self):
        """Test decoding with Rule B for binary 1."""
        angles = encode_3d_solids(1)
        result = decode_3d_solids_rule_b(angles)
        assert result == 1
    
    def test_decode_solids_rule_b_roundtrip(self):
        """Test encode-decode roundtrip with Rule B."""
        for b in [0, 1]:
            angles = encode_3d_solids(b)
            decoded = decode_3d_solids_rule_b(angles)
            assert decoded == b
    
    def test_decode_solids_rule_b_custom_threshold(self):
        """Test Rule B with custom threshold."""
        angles = (0.0, 0.0, 0.0, 0.0, 0.0)  # All cos = 1, sum = 5
        
        # With threshold 0, sum >= 0 → b = 0
        assert decode_3d_solids_rule_b(angles, threshold=0.0) == 0
        
        # With threshold 10, sum < 10 → b = 1
        assert decode_3d_solids_rule_b(angles, threshold=10.0) == 1


class TestVerifyTolerance:
    """Tests for verify_tolerance function."""
    
    def test_verify_tolerance_exact_match(self):
        """Test tolerance verification with exact match."""
        assert verify_tolerance(1.0, 1.0) is True
    
    def test_verify_tolerance_within_tolerance(self):
        """Test tolerance verification within EPSILON."""
        assert verify_tolerance(1.0, 1.0 + EPSILON * 0.5) is True
        assert verify_tolerance(1.0, 1.0 - EPSILON * 0.5) is True
    
    def test_verify_tolerance_at_boundary(self):
        """Test tolerance verification at exact boundary."""
        # Account for floating-point precision by testing very close to boundary
        assert verify_tolerance(1.0, 1.0 + EPSILON * 0.99) is True
        assert verify_tolerance(1.0, 1.0 - EPSILON * 0.99) is True
    
    def test_verify_tolerance_outside_tolerance(self):
        """Test tolerance verification outside EPSILON."""
        assert verify_tolerance(1.0, 1.0 + EPSILON * 2) is False
        assert verify_tolerance(1.0, 1.0 - EPSILON * 2) is False
    
    def test_verify_tolerance_custom_tolerance(self):
        """Test tolerance verification with custom tolerance."""
        custom_tol = 0.5
        assert verify_tolerance(1.0, 1.3, tolerance=custom_tol) is True
        assert verify_tolerance(1.0, 1.6, tolerance=custom_tol) is False


class TestIntegration:
    """Integration tests for the full codec system."""
    
    def test_2d_codec_multiple_values(self):
        """Test 2D codec with multiple encode-decode cycles."""
        for _ in range(10):
            for b in [0, 1]:
                point = encode_2d(b)
                decoded = decode_2d(point)
                assert decoded == b
    
    def test_seashell_codec_multiple_parameters(self):
        """Test seashell codec with various parameters."""
        params = [
            (1.0, 1.2, 1.0),
            (2.0, 1.5, 2.0),
            (0.5, 1.1, 0.5),
        ]
        
        for r0, phi, t in params:
            for b in [0, 1]:
                point = encode_3d_seashell(b, r0=r0, phi=phi, t=t)
                decoded = decode_3d_seashell(point)
                assert decoded == b
    
    def test_solids_codec_both_rules(self):
        """Test 5-solids codec with both decoding rules."""
        for b in [0, 1]:
            angles = encode_3d_solids(b)
            
            # Both rules should decode correctly
            decoded_a = decode_3d_solids_rule_a(angles)
            decoded_b = decode_3d_solids_rule_b(angles)
            
            assert decoded_a == b
            assert decoded_b == b
    
    def test_all_codecs_consistency(self):
        """Test that all codec methods are consistent."""
        for b in [0, 1]:
            # 2D codec
            point_2d = encode_2d(b)
            assert decode_2d(point_2d) == b
            
            # Seashell 3D codec
            point_3d_shell = encode_3d_seashell(b)
            assert decode_3d_seashell(point_3d_shell) == b
            
            # 5-solids 3D codec
            angles = encode_3d_solids(b)
            assert decode_3d_solids_rule_a(angles) == b
            assert decode_3d_solids_rule_b(angles) == b
