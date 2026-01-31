#!/usr/bin/env python3
"""
3D Codec for binary output using 5-solids frame methodology.

This module implements binary encoding using the contact points of 5 Platonic solids
and their stopping angles to generate deterministic binary bits.
"""

import math
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ContactPoint:
    """Represents a 3D contact point for a solid."""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'ContactPoint') -> float:
        """Calculate Euclidean distance to another contact point."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )


@dataclass
class FrameData:
    """Data for a single frame containing contact points for all 5 solids."""
    tetrahedron: ContactPoint
    cube: ContactPoint
    octahedron: ContactPoint
    dodecahedron: ContactPoint
    icosahedron: ContactPoint
    
    def get_all_contact_points(self) -> List[ContactPoint]:
        """Get all contact points in order: T, C, O, D, I."""
        return [
            self.tetrahedron,
            self.cube,
            self.octahedron,
            self.dodecahedron,
            self.icosahedron,
        ]


def wrap_angle(angle: float) -> float:
    """
    Normalize angle to [-π, π] range for circular angular differences.
    
    Args:
        angle: Angle in radians
        
    Returns:
        Normalized angle in [-π, π]
    """
    # Normalize to [-π, π]
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def compute_stopping_angle(contact: ContactPoint) -> float:
    """
    Compute stopping angle α_s = atan2(y_s, x_s) for a solid's contact point.
    
    Args:
        contact: Contact point with x, y, z coordinates
        
    Returns:
        Stopping angle in radians
    """
    return math.atan2(contact.y, contact.x)


def compute_bit_rule_a(angles: List[float]) -> int:
    """
    Compute binary bit using Rule A (Majority voting).
    
    Rule A: For each solid, compute vote_s = 0 if cos(α_s) ≥ 0 else 1.
    The bit is decided as bit = 1 if Σ vote_s ≥ 3 else 0.
    
    Args:
        angles: List of 5 stopping angles (one per solid)
        
    Returns:
        Binary bit (0 or 1)
    """
    if len(angles) != 5:
        raise ValueError("Rule A requires exactly 5 angles")
    
    votes = sum(1 if math.cos(angle) < 0 else 0 for angle in angles)
    return 1 if votes >= 3 else 0


def compute_bit_rule_b(angles: List[float]) -> int:
    """
    Compute binary bit using Rule B (Threshold).
    
    Rule B: Compute sum S = Σ cos(α_s). The bit is bit = 0 if S ≥ 0 else 1.
    
    Args:
        angles: List of 5 stopping angles (one per solid)
        
    Returns:
        Binary bit (0 or 1)
    """
    if len(angles) != 5:
        raise ValueError("Rule B requires exactly 5 angles")
    
    cosine_sum = sum(math.cos(angle) for angle in angles)
    return 0 if cosine_sum >= 0 else 1


def encode_frame_to_bit(frame: FrameData) -> Tuple[int, int, List[float]]:
    """
    Encode a frame to a binary bit using both Rule A and Rule B.
    
    Args:
        frame: Frame data containing contact points for all 5 solids
        
    Returns:
        Tuple of (bit_rule_a, bit_rule_b, stopping_angles)
    """
    contact_points = frame.get_all_contact_points()
    stopping_angles = [compute_stopping_angle(cp) for cp in contact_points]
    
    bit_a = compute_bit_rule_a(stopping_angles)
    bit_b = compute_bit_rule_b(stopping_angles)
    
    return bit_a, bit_b, stopping_angles


def verify_repeatability(
    frame1: FrameData,
    frame2: FrameData,
    epsilon: float = 0.08
) -> Tuple[bool, List[str]]:
    """
    Verify that two frames are repeatable within tolerance ε.
    
    For all repeated runs, check that outcomes are stable:
    ||v_s − v'_s||₂ ≤ ε for all solids.
    
    Args:
        frame1: First frame data
        frame2: Second frame data
        epsilon: Tolerance for repeatability (default 0.08)
        
    Returns:
        Tuple of (is_repeatable, error_messages)
    """
    errors = []
    contacts1 = frame1.get_all_contact_points()
    contacts2 = frame2.get_all_contact_points()
    
    solid_names = ["Tetrahedron", "Cube", "Octahedron", "Dodecahedron", "Icosahedron"]
    
    for i, (c1, c2, name) in enumerate(zip(contacts1, contacts2, solid_names)):
        distance = c1.distance_to(c2)
        if distance > epsilon:
            errors.append(
                f"{name}: distance {distance:.4f} exceeds tolerance {epsilon} "
                f"(v1={c1.x:.4f},{c1.y:.4f},{c1.z:.4f}, "
                f"v2={c2.x:.4f},{c2.y:.4f},{c2.z:.4f})"
            )
    
    return len(errors) == 0, errors


def verify_rule_agreement(
    bit_a: int,
    bit_b: int,
    allow_disagreement: bool = False
) -> Tuple[bool, Optional[str]]:
    """
    Verify that Rule A and Rule B agree on the output bit.
    
    Args:
        bit_a: Bit from Rule A
        bit_b: Bit from Rule B
        allow_disagreement: If True, disagreement is allowed (for erasure/retransmission)
        
    Returns:
        Tuple of (rules_agree, error_message)
    """
    if bit_a == bit_b:
        return True, None
    
    if allow_disagreement:
        return False, "Rules disagree but disagreement is allowed (erasure mode)"
    
    return False, f"Rule A ({bit_a}) and Rule B ({bit_b}) disagree"


def process_frame(
    frame: FrameData,
    previous_frame: Optional[FrameData] = None,
    epsilon: float = 0.08,
    allow_rule_disagreement: bool = False
) -> Tuple[int, bool, List[str]]:
    """
    Process a frame to produce a binary bit with full verification.
    
    Args:
        frame: Frame data to process
        previous_frame: Optional previous frame for repeatability check
        epsilon: Tolerance for repeatability verification
        allow_rule_disagreement: Whether to allow Rule A/B disagreement
        
    Returns:
        Tuple of (output_bit, is_valid, error_messages)
            - output_bit: The consensus bit (from Rule A if rules agree, -1 if invalid)
            - is_valid: True if all verification passes
            - error_messages: List of any verification errors
    """
    errors = []
    
    # Encode frame to bit using both rules
    bit_a, bit_b, angles = encode_frame_to_bit(frame)
    
    # Check rule agreement
    rules_agree, agreement_error = verify_rule_agreement(
        bit_a, bit_b, allow_rule_disagreement
    )
    if agreement_error:
        errors.append(agreement_error)
    
    # Check repeatability if previous frame provided
    if previous_frame is not None:
        is_repeatable, repeat_errors = verify_repeatability(
            previous_frame, frame, epsilon
        )
        if not is_repeatable:
            errors.extend(repeat_errors)
    
    # Determine output bit and validity
    # Valid if no errors, or only error is rule disagreement and that's allowed
    has_only_rule_error = (
        len(errors) == 1 and 
        agreement_error is not None and 
        errors[0] == agreement_error
    )
    is_valid = len(errors) == 0 or (allow_rule_disagreement and has_only_rule_error)
    output_bit = bit_a if rules_agree else -1
    
    return output_bit, is_valid, errors
