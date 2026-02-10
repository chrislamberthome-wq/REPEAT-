"""Verification modules for spintronics experimental packets."""

from .verify_state_survival_macrospin import (
    verify_spin_configuration,
    verify_state_survival,
    compute_nearest_neighbor_energy,
)

from .verify_trace_integrity import (
    verify_trace_integrity,
    verify_pulse_sequence,
    compute_trace_checksum,
)

from .verify_mram_write_read import (
    verify_mram_write_read,
    verify_threshold_parameters,
    decode_resistance_to_bit,
)

__all__ = [
    "verify_spin_configuration",
    "verify_state_survival",
    "compute_nearest_neighbor_energy",
    "verify_trace_integrity",
    "verify_pulse_sequence",
    "compute_trace_checksum",
    "verify_mram_write_read",
    "verify_threshold_parameters",
    "decode_resistance_to_bit",
]
