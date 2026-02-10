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

# Export spintronics functions
from repeat_hd.spintronics import (
    # Data structures
    SpinSymbol,
    SpinExperiment,
    SpinReading,
    VerificationResult,
    TracePacket,
    # REPEAT protocol functions
    encode_spin_symbol,
    encode_experiment,
    decode_spin_reading,
    verify_bloch_sphere_survival,
    verify_pulse_integrity,
    verify_task_outcome,
    compute_trace_hash,
    create_receipt,
    run_repeat_protocol,
)

__all__ = [
    # 3D codec
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
    # Spintronics
    "SpinSymbol",
    "SpinExperiment",
    "SpinReading",
    "VerificationResult",
    "TracePacket",
    "encode_spin_symbol",
    "encode_experiment",
    "decode_spin_reading",
    "verify_bloch_sphere_survival",
    "verify_pulse_integrity",
    "verify_task_outcome",
    "compute_trace_hash",
    "create_receipt",
    "run_repeat_protocol",
]

