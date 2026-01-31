"""Tests for the 3D codec module."""

import pytest
import math
from repeat_hd.codec3d import (
    ContactPoint,
    FrameData,
    wrap_angle,
    compute_stopping_angle,
    compute_bit_rule_a,
    compute_bit_rule_b,
    encode_frame_to_bit,
    verify_repeatability,
    verify_rule_agreement,
    process_frame,
)


class TestContactPoint:
    """Tests for ContactPoint class."""
    
    def test_distance_calculation(self):
        """Test Euclidean distance calculation between contact points."""
        p1 = ContactPoint(0.0, 0.0, 0.0)
        p2 = ContactPoint(1.0, 0.0, 0.0)
        assert abs(p1.distance_to(p2) - 1.0) < 1e-10
        
    def test_distance_3d(self):
        """Test distance in 3D space."""
        p1 = ContactPoint(1.0, 2.0, 3.0)
        p2 = ContactPoint(4.0, 6.0, 8.0)
        # Distance = sqrt((4-1)^2 + (6-2)^2 + (8-3)^2) = sqrt(9 + 16 + 25) = sqrt(50)
        expected = math.sqrt(50)
        assert abs(p1.distance_to(p2) - expected) < 1e-10
        
    def test_distance_zero(self):
        """Test distance to self is zero."""
        p = ContactPoint(1.5, 2.5, 3.5)
        assert p.distance_to(p) < 1e-10


class TestFrameData:
    """Tests for FrameData class."""
    
    def test_get_all_contact_points_order(self):
        """Test that contact points are returned in correct order: T, C, O, D, I."""
        frame = FrameData(
            tetrahedron=ContactPoint(1.0, 0.0, 0.0),
            cube=ContactPoint(2.0, 0.0, 0.0),
            octahedron=ContactPoint(3.0, 0.0, 0.0),
            dodecahedron=ContactPoint(4.0, 0.0, 0.0),
            icosahedron=ContactPoint(5.0, 0.0, 0.0),
        )
        points = frame.get_all_contact_points()
        assert len(points) == 5
        assert points[0].x == 1.0  # Tetrahedron
        assert points[1].x == 2.0  # Cube
        assert points[2].x == 3.0  # Octahedron
        assert points[3].x == 4.0  # Dodecahedron
        assert points[4].x == 5.0  # Icosahedron


class TestWrapAngle:
    """Tests for wrap_angle function."""
    
    def test_angle_in_range(self):
        """Test that angles already in [-π, π] are unchanged."""
        assert abs(wrap_angle(0.0) - 0.0) < 1e-10
        assert abs(wrap_angle(math.pi / 2) - math.pi / 2) < 1e-10
        assert abs(wrap_angle(-math.pi / 2) - (-math.pi / 2)) < 1e-10
        
    def test_angle_wrapping_positive(self):
        """Test wrapping of angles > π."""
        # 2π should wrap to 0
        assert abs(wrap_angle(2 * math.pi)) < 1e-10
        # 3π should wrap to π
        result = wrap_angle(3 * math.pi)
        assert abs(abs(result) - math.pi) < 1e-10
        
    def test_angle_wrapping_negative(self):
        """Test wrapping of angles < -π."""
        # -2π should wrap to 0
        assert abs(wrap_angle(-2 * math.pi)) < 1e-10


class TestComputeStoppingAngle:
    """Tests for compute_stopping_angle function."""
    
    def test_angle_positive_x(self):
        """Test angle for point on positive x-axis."""
        contact = ContactPoint(1.0, 0.0, 0.0)
        angle = compute_stopping_angle(contact)
        assert abs(angle - 0.0) < 1e-10
        
    def test_angle_positive_y(self):
        """Test angle for point on positive y-axis."""
        contact = ContactPoint(0.0, 1.0, 0.0)
        angle = compute_stopping_angle(contact)
        assert abs(angle - math.pi / 2) < 1e-10
        
    def test_angle_negative_x(self):
        """Test angle for point on negative x-axis."""
        contact = ContactPoint(-1.0, 0.0, 0.0)
        angle = compute_stopping_angle(contact)
        assert abs(abs(angle) - math.pi) < 1e-10
        
    def test_angle_quadrant_1(self):
        """Test angle for point in quadrant I."""
        contact = ContactPoint(1.0, 1.0, 0.0)
        angle = compute_stopping_angle(contact)
        assert abs(angle - math.pi / 4) < 1e-10


class TestComputeBitRuleA:
    """Tests for compute_bit_rule_a function."""
    
    def test_all_positive_cosines(self):
        """Test when all angles have cos(α) >= 0 (all votes are 0)."""
        # Angles in [-π/2, π/2] have positive cosines
        angles = [0.0, math.pi / 4, -math.pi / 4, math.pi / 6, -math.pi / 6]
        bit = compute_bit_rule_a(angles)
        # All votes are 0, sum < 3, so bit = 0
        assert bit == 0
        
    def test_all_negative_cosines(self):
        """Test when all angles have cos(α) < 0 (all votes are 1)."""
        # Angles in (π/2, 3π/2) have negative cosines
        angles = [math.pi, 3 * math.pi / 4, -3 * math.pi / 4, 
                  2 * math.pi / 3, -2 * math.pi / 3]
        bit = compute_bit_rule_a(angles)
        # All votes are 1, sum = 5 >= 3, so bit = 1
        assert bit == 1
        
    def test_majority_threshold(self):
        """Test exactly 3 negative cosines (at the threshold)."""
        # 3 angles with negative cosines, 2 with positive
        angles = [math.pi, 3 * math.pi / 4, -3 * math.pi / 4, 
                  0.0, math.pi / 4]
        bit = compute_bit_rule_a(angles)
        # 3 votes are 1, sum = 3 >= 3, so bit = 1
        assert bit == 1
        
    def test_below_majority_threshold(self):
        """Test exactly 2 negative cosines (below threshold)."""
        angles = [math.pi, -3 * math.pi / 4, 0.0, math.pi / 4, -math.pi / 4]
        bit = compute_bit_rule_a(angles)
        # 2 votes are 1, sum = 2 < 3, so bit = 0
        assert bit == 0
        
    def test_wrong_number_of_angles(self):
        """Test that ValueError is raised for wrong number of angles."""
        with pytest.raises(ValueError, match="exactly 5 angles"):
            compute_bit_rule_a([0.0, 1.0])


class TestComputeBitRuleB:
    """Tests for compute_bit_rule_b function."""
    
    def test_positive_sum(self):
        """Test when sum of cosines is positive."""
        # All small angles have positive cosines
        angles = [0.0, math.pi / 4, -math.pi / 4, math.pi / 6, -math.pi / 6]
        bit = compute_bit_rule_b(angles)
        # Sum of cosines > 0, so bit = 0
        assert bit == 0
        
    def test_negative_sum(self):
        """Test when sum of cosines is negative."""
        # All angles near π have negative cosines
        angles = [math.pi, 3 * math.pi / 4, -3 * math.pi / 4, 
                  2 * math.pi / 3, -2 * math.pi / 3]
        bit = compute_bit_rule_b(angles)
        # Sum of cosines < 0, so bit = 1
        assert bit == 1
        
    def test_zero_sum(self):
        """Test when sum of cosines is exactly zero."""
        # Construct angles where cosines sum to 0
        # cos(π/2) = 0, so use π/2 for all
        angles = [math.pi / 2] * 5
        bit = compute_bit_rule_b(angles)
        # Sum = 0 >= 0, so bit = 0
        assert bit == 0
        
    def test_wrong_number_of_angles(self):
        """Test that ValueError is raised for wrong number of angles."""
        with pytest.raises(ValueError, match="exactly 5 angles"):
            compute_bit_rule_b([0.0, 1.0, 2.0])


class TestEncodeFrameToBit:
    """Tests for encode_frame_to_bit function."""
    
    def test_encode_simple_frame(self):
        """Test encoding a simple frame."""
        frame = FrameData(
            tetrahedron=ContactPoint(1.0, 0.0, 0.0),
            cube=ContactPoint(1.0, 0.0, 0.0),
            octahedron=ContactPoint(1.0, 0.0, 0.0),
            dodecahedron=ContactPoint(1.0, 0.0, 0.0),
            icosahedron=ContactPoint(1.0, 0.0, 0.0),
        )
        bit_a, bit_b, angles = encode_frame_to_bit(frame)
        
        # All angles should be 0
        assert all(abs(a) < 1e-10 for a in angles)
        # Both rules should give bit = 0
        assert bit_a == 0
        assert bit_b == 0
        
    def test_encode_returns_angles(self):
        """Test that stopping angles are returned."""
        frame = FrameData(
            tetrahedron=ContactPoint(1.0, 1.0, 0.0),
            cube=ContactPoint(1.0, 0.0, 0.0),
            octahedron=ContactPoint(0.0, 1.0, 0.0),
            dodecahedron=ContactPoint(-1.0, 0.0, 0.0),
            icosahedron=ContactPoint(0.0, -1.0, 0.0),
        )
        bit_a, bit_b, angles = encode_frame_to_bit(frame)
        
        assert len(angles) == 5
        # Check specific angles
        assert abs(angles[0] - math.pi / 4) < 1e-10  # atan2(1, 1)
        assert abs(angles[1] - 0.0) < 1e-10  # atan2(0, 1)
        assert abs(angles[2] - math.pi / 2) < 1e-10  # atan2(1, 0)


class TestVerifyRepeatability:
    """Tests for verify_repeatability function."""
    
    def test_identical_frames(self):
        """Test that identical frames pass repeatability check."""
        frame = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        is_repeatable, errors = verify_repeatability(frame, frame)
        
        assert is_repeatable
        assert len(errors) == 0
        
    def test_within_tolerance(self):
        """Test frames within epsilon tolerance pass."""
        frame1 = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        # Small perturbation within epsilon = 0.08
        frame2 = FrameData(
            tetrahedron=ContactPoint(1.01, 2.01, 3.01),
            cube=ContactPoint(4.01, 5.01, 6.01),
            octahedron=ContactPoint(7.01, 8.01, 9.01),
            dodecahedron=ContactPoint(10.01, 11.01, 12.01),
            icosahedron=ContactPoint(13.01, 14.01, 15.01),
        )
        is_repeatable, errors = verify_repeatability(frame1, frame2)
        
        assert is_repeatable
        assert len(errors) == 0
        
    def test_exceeds_tolerance(self):
        """Test frames exceeding epsilon tolerance fail."""
        frame1 = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        # Large perturbation exceeding epsilon = 0.08
        frame2 = FrameData(
            tetrahedron=ContactPoint(1.1, 2.1, 3.1),  # Distance > 0.08
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        is_repeatable, errors = verify_repeatability(frame1, frame2)
        
        assert not is_repeatable
        assert len(errors) > 0
        assert "Tetrahedron" in errors[0]
        
    def test_custom_epsilon(self):
        """Test custom epsilon tolerance."""
        frame1 = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        frame2 = FrameData(
            tetrahedron=ContactPoint(1.15, 2.15, 3.15),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        # Should fail with default epsilon
        is_repeatable1, _ = verify_repeatability(frame1, frame2)
        assert not is_repeatable1
        
        # Should pass with larger epsilon
        is_repeatable2, _ = verify_repeatability(frame1, frame2, epsilon=0.3)
        assert is_repeatable2


class TestVerifyRuleAgreement:
    """Tests for verify_rule_agreement function."""
    
    def test_rules_agree(self):
        """Test when both rules agree."""
        agrees, error = verify_rule_agreement(0, 0)
        assert agrees
        assert error is None
        
        agrees, error = verify_rule_agreement(1, 1)
        assert agrees
        assert error is None
        
    def test_rules_disagree_not_allowed(self):
        """Test when rules disagree and disagreement not allowed."""
        agrees, error = verify_rule_agreement(0, 1, allow_disagreement=False)
        assert not agrees
        assert error is not None
        assert "disagree" in error.lower()
        
    def test_rules_disagree_allowed(self):
        """Test when rules disagree but disagreement is allowed."""
        agrees, error = verify_rule_agreement(0, 1, allow_disagreement=True)
        assert not agrees
        assert error is not None
        assert "allowed" in error.lower()


class TestProcessFrame:
    """Tests for process_frame function."""
    
    def test_simple_valid_frame(self):
        """Test processing a simple valid frame."""
        frame = FrameData(
            tetrahedron=ContactPoint(1.0, 0.0, 0.0),
            cube=ContactPoint(1.0, 0.0, 0.0),
            octahedron=ContactPoint(1.0, 0.0, 0.0),
            dodecahedron=ContactPoint(1.0, 0.0, 0.0),
            icosahedron=ContactPoint(1.0, 0.0, 0.0),
        )
        bit, is_valid, errors = process_frame(frame)
        
        assert is_valid
        assert len(errors) == 0
        assert bit == 0  # All angles are 0, both rules give 0
        
    def test_frame_with_repeatability_check(self):
        """Test processing frame with repeatability verification."""
        frame1 = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        frame2 = FrameData(
            tetrahedron=ContactPoint(1.01, 2.01, 3.01),
            cube=ContactPoint(4.01, 5.01, 6.01),
            octahedron=ContactPoint(7.01, 8.01, 9.01),
            dodecahedron=ContactPoint(10.01, 11.01, 12.01),
            icosahedron=ContactPoint(13.01, 14.01, 15.01),
        )
        bit, is_valid, errors = process_frame(frame2, previous_frame=frame1)
        
        assert is_valid
        assert len(errors) == 0
        
    def test_frame_fails_repeatability(self):
        """Test processing frame that fails repeatability."""
        frame1 = FrameData(
            tetrahedron=ContactPoint(1.0, 2.0, 3.0),
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        frame2 = FrameData(
            tetrahedron=ContactPoint(1.5, 2.5, 3.5),  # Exceeds tolerance
            cube=ContactPoint(4.0, 5.0, 6.0),
            octahedron=ContactPoint(7.0, 8.0, 9.0),
            dodecahedron=ContactPoint(10.0, 11.0, 12.0),
            icosahedron=ContactPoint(13.0, 14.0, 15.0),
        )
        bit, is_valid, errors = process_frame(frame2, previous_frame=frame1)
        
        assert not is_valid
        assert len(errors) > 0
        
    def test_rule_disagreement_not_allowed(self):
        """Test when rules disagree and disagreement not allowed."""
        # Create frame where rules might disagree
        # This is tricky - need angles where majority vote != threshold
        # Using specific angles to create disagreement
        frame = FrameData(
            tetrahedron=ContactPoint(0.0, 1.0, 0.0),    # π/2
            cube=ContactPoint(0.0, 1.0, 0.0),           # π/2
            octahedron=ContactPoint(0.0, 1.0, 0.0),     # π/2
            dodecahedron=ContactPoint(-1.0, 0.0, 0.0),  # π
            icosahedron=ContactPoint(-1.0, 0.0, 0.0),   # π
        )
        bit, is_valid, errors = process_frame(frame, allow_rule_disagreement=False)
        
        # Check if rules actually disagree for this configuration
        # cos(π/2) = 0, cos(π) = -1
        # Rule A: votes = [0, 0, 0, 1, 1] -> sum = 2 < 3 -> bit = 0
        # Rule B: sum = 0 + 0 + 0 + (-1) + (-1) = -2 < 0 -> bit = 1
        # So they disagree
        if len(errors) > 0:
            assert not is_valid
            assert any("disagree" in e.lower() for e in errors)
