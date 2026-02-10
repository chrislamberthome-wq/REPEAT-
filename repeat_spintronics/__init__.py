"""REPEAT Spintronics MRAM MVP: Magnetization texture encoding with verifier proofs."""

__version__ = "0.1.0"

from repeat_spintronics.encoder import (
    encode_to_magnetization,
    decode_from_magnetization,
)
from repeat_spintronics.packetizer import (
    create_mram_packet,
    read_mram_packet,
    verify_packet_receipt,
)

__all__ = [
    "encode_to_magnetization",
    "decode_from_magnetization",
    "create_mram_packet",
    "read_mram_packet",
    "verify_packet_receipt",
]
