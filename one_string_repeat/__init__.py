"""
one_string_REPEAT v1.0 — canonical run certifying primitive.

Provides a closed certifying loop:
    canonicalize(payload) -> payload_bytes
    -> sha256 + crc16 -> execute -> run_receipt
    -> replay -> compare -> verification_receipt

PASS / FAIL / ERROR are the only admissible truth states.
"""
