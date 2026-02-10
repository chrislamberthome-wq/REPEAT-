"""Spintronics REPEAT + Platoputer Protocol.

This module implements spintronics-ready experimental packet handling
with MRAM MVP for fast scientific adoption.
"""

__version__ = "0.1.0"

from .canonical import canonicalize_json, validate_canonical_form, normalize_packet
from .hash import (
    hash_packet,
    hash_trace,
    compute_receipt_hash,
    verify_checksum
)

__all__ = [
    "canonicalize_json",
    "validate_canonical_form", 
    "normalize_packet",
    "hash_packet",
    "hash_trace",
    "compute_receipt_hash",
    "verify_checksum",
]
