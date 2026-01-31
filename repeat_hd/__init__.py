"""REPEAT-HD: A data encoding and verification library."""

__version__ = "0.1.0"

# Export 3D codec functions for easy access
from repeat_hd.codec_3d import (
    # Helper functions
    wrap_angle,
    verify_tolerance,
    # 2D codec
    encode_2d,
    decode_2d,
    # 3D seashell codec
    encode_3d_seashell,
    decode_3d_seashell,
    # 3D 5-solids codec
    encode_3d_solids,
    decode_3d_solids_rule_a,
    decode_3d_solids_rule_b,
    # Constants
    EPSILON,
    DEFAULT_RADIUS,
)

__all__ = [
    "wrap_angle",
    "verify_tolerance",
    "encode_2d",
    "decode_2d",
    "encode_3d_seashell",
    "decode_3d_seashell",
    "encode_3d_solids",
    "decode_3d_solids_rule_a",
    "decode_3d_solids_rule_b",
    "EPSILON",
    "DEFAULT_RADIUS",
]

