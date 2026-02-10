"""Encoder for Platoputer to magnetization textures using tetrahedron-based codebooks.

This module provides encoding and decoding between Platoputer data and magnetization
textures using the tetrahedron (minimal multi-state) representation from the 5 Platonic
solids framework.
"""

import math
from typing import List, Tuple, Optional
from repeat_hd.codec_3d import encode_3d_solids, decode_3d_solids_rule_a


# Magnetization state representation
# Each magnetization texture is represented by 5 angles from Platonic solids
# The tetrahedron angle is the primary state indicator (minimal multi-state)
MagnetizationTexture = Tuple[float, float, float, float, float]


def encode_to_magnetization(binary_data: bytes) -> List[MagnetizationTexture]:
    """
    Encode binary data to magnetization textures using tetrahedron-based codebooks.
    
    Each byte is converted to 8 magnetization textures (one per bit).
    Uses the 5 Platonic solids encoding with tetrahedron as the primary state.
    
    Args:
        binary_data: Binary data to encode
        
    Returns:
        List of magnetization textures (5-angle tuples)
        
    Example:
        >>> data = b"A"  # 0x41 = 01000001
        >>> textures = encode_to_magnetization(data)
        >>> len(textures)
        8
    """
    textures = []
    
    for byte in binary_data:
        # Process each bit in the byte (MSB first)
        for bit_pos in range(7, -1, -1):
            bit = (byte >> bit_pos) & 1
            # Encode bit using 5-solids frame (includes tetrahedron)
            texture = encode_3d_solids(bit)
            textures.append(texture)
    
    return textures


def decode_from_magnetization(textures: List[MagnetizationTexture]) -> Optional[bytes]:
    """
    Decode magnetization textures back to binary data.
    
    Decodes magnetization textures using tetrahedron-based codebook with majority voting.
    
    Args:
        textures: List of magnetization textures (5-angle tuples)
        
    Returns:
        Decoded binary data, or None if decoding fails
        
    Example:
        >>> data = b"Test"
        >>> textures = encode_to_magnetization(data)
        >>> decoded = decode_from_magnetization(textures)
        >>> decoded == data
        True
    """
    if not textures:
        return b""
    
    # Validate texture count is multiple of 8 (full bytes)
    if len(textures) % 8 != 0:
        return None
    
    bytes_list = []
    
    # Process textures in groups of 8 (one byte)
    for byte_idx in range(0, len(textures), 8):
        byte_value = 0
        
        for bit_idx in range(8):
            texture = textures[byte_idx + bit_idx]
            # Decode bit using majority voting rule
            bit = decode_3d_solids_rule_a(texture)
            
            # Set bit in byte (MSB first, so bit 0 goes to position 7)
            byte_value |= (bit << (7 - bit_idx))
        
        bytes_list.append(byte_value)
    
    return bytes(bytes_list)


def get_tetrahedron_state(texture: MagnetizationTexture) -> int:
    """
    Extract the tetrahedron state (minimal multi-state indicator) from magnetization texture.
    
    The tetrahedron angle is the first component of the 5-angle tuple and serves
    as the primary state indicator in the minimal multi-state representation.
    
    Args:
        texture: Magnetization texture (5-angle tuple)
        
    Returns:
        Binary state (0 or 1) based on tetrahedron angle
    """
    alpha_T = texture[0]  # Tetrahedron angle
    # State is 0 if cos(α_T) >= 0, else 1
    return 0 if math.cos(alpha_T) >= 0 else 1
