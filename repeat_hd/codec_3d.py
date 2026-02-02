"""3D Codec System for encoding/decoding binary messages with geometric representations."""

import math
from typing import Tuple, Optional


# Constants
EPSILON = 0.08  # Tolerance threshold for verification
DEFAULT_RADIUS = 1.0  # Default radius for 2D encoding


def wrap_angle(delta_theta: float) -> float:
    """
    Compute minimum angular distance.
    
    Wraps angle to [-π, π] range to find shortest angular distance.
    
    Args:
        delta_theta: Angular difference in radians
        
    Returns:
        Wrapped angle in range [-π, π]
    """
    # Normalize to [-π, π] range
    while delta_theta > math.pi:
        delta_theta -= 2 * math.pi
    while delta_theta < -math.pi:
        delta_theta += 2 * math.pi
    return delta_theta


def encode_2d(binary_input: int, radius: float = DEFAULT_RADIUS) -> Tuple[float, float]:
    """
    Encode binary input to 2D point using polar coordinates.
    
    Maps binary value to angle θ:
    - b = 0 → θ = 0
    - b = 1 → θ = π
    
    Output point: p2 = (R cos θ, R sin θ)
    
    Args:
        binary_input: Binary value (0 or 1)
        radius: Radius for polar encoding (default: 1.0)
        
    Returns:
        Tuple of (x, y) coordinates
        
    Raises:
        ValueError: If binary_input is not 0 or 1
    """
    if binary_input not in [0, 1]:
        raise ValueError(f"Binary input must be 0 or 1, got {binary_input}")
    
    # Map binary to angle
    theta = 0.0 if binary_input == 0 else math.pi
    
    # Convert to cartesian coordinates
    x = radius * math.cos(theta)
    y = radius * math.sin(theta)
    
    return (x, y)


def decode_2d(point: Tuple[float, float], radius: float = DEFAULT_RADIUS, 
              tolerance: float = EPSILON) -> Optional[int]:
    """
    Decode binary value from 2D point with tolerance verification.
    
    Extracts binary value by checking angle θ:
    - θ ≈ 0 → b = 0
    - θ ≈ π → b = 1
    
    Args:
        point: Tuple of (x, y) coordinates
        radius: Expected radius (default: 1.0)
        tolerance: Tolerance threshold for verification (default: 0.08)
        
    Returns:
        Decoded binary value (0 or 1), or None if verification fails
    """
    x, y = point
    
    # Check if point is approximately on the expected circle
    distance = math.sqrt(x*x + y*y)
    if abs(distance - radius) > tolerance:
        return None
    
    # Compute angle
    theta = math.atan2(y, x)
    
    # Check which angle it's closest to
    # For b=0: θ=0, for b=1: θ=π
    dist_to_0 = abs(wrap_angle(theta - 0.0))
    dist_to_pi = abs(wrap_angle(theta - math.pi))
    
    if dist_to_0 < tolerance:
        return 0
    elif dist_to_pi < tolerance:
        return 1
    else:
        # Point doesn't match either expected angle
        return None


def encode_3d_seashell(binary_input: int, r0: float = 1.0, phi: float = 1.2, 
                       t: float = 1.0) -> Tuple[float, float, float]:
    """
    Encode binary input to 3D point using logarithmic spiral (seashell curve).
    
    The seashell curve is based on r0 * φ^t with z modulated by binary value:
    - b = 0 → z moves down (negative)
    - b = 1 → z moves up (positive)
    
    Args:
        binary_input: Binary value (0 or 1)
        r0: Base radius parameter (default: 1.0)
        phi: Growth factor (default: 1.2)
        t: Time/angle parameter (default: 1.0)
        
    Returns:
        Tuple of (x, y, z) coordinates
        
    Raises:
        ValueError: If binary_input is not 0 or 1
    """
    if binary_input not in [0, 1]:
        raise ValueError(f"Binary input must be 0 or 1, got {binary_input}")
    
    # Compute radius based on logarithmic spiral
    r = r0 * (phi ** t)
    
    # Compute x, y using polar coordinates with angle t
    x = r * math.cos(t)
    y = r * math.sin(t)
    
    # Modulate z based on binary value
    # b=0 → z negative, b=1 → z positive
    z = -r if binary_input == 0 else r
    
    return (x, y, z)


def decode_3d_seashell(point: Tuple[float, float, float]) -> int:
    """
    Decode binary value from 3D seashell curve point.
    
    Decodes by checking the sign of z:
    - z < 0 → b = 0
    - z ≥ 0 → b = 1
    
    Args:
        point: Tuple of (x, y, z) coordinates
        
    Returns:
        Decoded binary value (0 or 1)
    """
    _, _, z = point
    return 0 if z < 0 else 1


def encode_3d_solids(binary_input: int) -> Tuple[float, float, float, float, float]:
    """
    Encode binary input using 5 Platonic solids frame.
    
    Returns stopping angles (α_T, α_C, α_O, α_D, α_I) for:
    - Tetrahedron (T)
    - Cube (C)
    - Octahedron (O)
    - Dodecahedron (D)
    - Icosahedron (I)
    
    The angles are computed based on the binary input and geometric properties
    of each Platonic solid.
    
    Args:
        binary_input: Binary value (0 or 1)
        
    Returns:
        Tuple of 5 stopping angles (α_T, α_C, α_O, α_D, α_I)
        
    Raises:
        ValueError: If binary_input is not 0 or 1
    """
    if binary_input not in [0, 1]:
        raise ValueError(f"Binary input must be 0 or 1, got {binary_input}")
    
    # Base angles for each Platonic solid (characteristic angles in radians)
    # These are related to the dihedral angles and symmetries
    
    if binary_input == 0:
        # For b=0: angles that will produce cos(α) >= 0 for majority
        alpha_T = 0.0  # Tetrahedron: cos(0) = 1
        alpha_C = math.pi / 6  # Cube: cos(π/6) ≈ 0.866
        alpha_O = math.pi / 4  # Octahedron: cos(π/4) ≈ 0.707
        alpha_D = math.pi / 3  # Dodecahedron: cos(π/3) = 0.5
        alpha_I = 0.4  # Icosahedron: cos(0.4) ≈ 0.921
    else:  # binary_input == 1
        # For b=1: angles that will produce cos(α) < 0 for majority
        alpha_T = 2.0 * math.pi / 3  # Tetrahedron: cos(2π/3) = -0.5
        alpha_C = 3.0 * math.pi / 4  # Cube: cos(3π/4) ≈ -0.707
        alpha_O = 5.0 * math.pi / 6  # Octahedron: cos(5π/6) ≈ -0.866
        alpha_D = math.pi  # Dodecahedron: cos(π) = -1
        alpha_I = 2.5  # Icosahedron: cos(2.5) ≈ -0.801
    
    return (alpha_T, alpha_C, alpha_O, alpha_D, alpha_I)


def decode_3d_solids_rule_a(angles: Tuple[float, float, float, float, float]) -> int:
    """
    Decode binary value from 5-solids angles using Rule A (majority voting).
    
    Rule A: For each solid s, compute vote_s = 0 if cos(α_s) ≥ 0 else 1
    Then take majority vote.
    
    Args:
        angles: Tuple of 5 stopping angles (α_T, α_C, α_O, α_D, α_I)
        
    Returns:
        Decoded binary value (0 or 1) based on majority vote
    """
    votes = []
    for alpha in angles:
        vote = 0 if math.cos(alpha) >= 0 else 1
        votes.append(vote)
    
    # Return majority vote
    return 1 if sum(votes) > len(votes) / 2 else 0


def decode_3d_solids_rule_b(angles: Tuple[float, float, float, float, float], 
                            threshold: float = 0.0) -> int:
    """
    Decode binary value from 5-solids angles using Rule B (sum threshold).
    
    Rule B: Compute S = Σ cos(α_s) for all solids
    - If S ≥ threshold → b = 0
    - If S < threshold → b = 1
    
    Args:
        angles: Tuple of 5 stopping angles (α_T, α_C, α_O, α_D, α_I)
        threshold: Threshold value (default: 0.0)
        
    Returns:
        Decoded binary value (0 or 1) based on sum threshold
    """
    cosine_sum = sum(math.cos(alpha) for alpha in angles)
    return 0 if cosine_sum >= threshold else 1


def verify_tolerance(expected: float, actual: float, tolerance: float = EPSILON) -> bool:
    """
    Verify that actual value is within tolerance of expected value.
    
    Args:
        expected: Expected value
        actual: Actual value
        tolerance: Tolerance threshold (default: 0.08)
        
    Returns:
        True if |expected - actual| <= tolerance, False otherwise
    """
    return abs(expected - actual) <= tolerance
