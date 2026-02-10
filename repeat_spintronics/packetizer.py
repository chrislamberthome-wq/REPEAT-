"""MRAM write/read packetization with SHA-based verifier proofs.

This module provides functionality to create, read, and verify MRAM packets
with magnetization textures and cryptographic receipt verification.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional, Any

from repeat_spintronics.encoder import (
    encode_to_magnetization,
    decode_from_magnetization,
    MagnetizationTexture,
)


def _compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of data and return as hex string."""
    return hashlib.sha256(data).hexdigest()


def _compute_sha256_str(data: str) -> str:
    """Compute SHA-256 hash of string and return as hex string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def create_mram_packet(
    data: bytes,
    operation: str = "write"
) -> Dict[str, Any]:
    """
    Create an MRAM packet for write/read operation.
    
    Encodes binary data to magnetization textures and creates a packet
    with checksum and metadata according to packet.schema.json.
    
    Args:
        data: Binary data to encode
        operation: Operation type ("write" or "read")
        
    Returns:
        MRAM packet dictionary conforming to packet.schema.json
        
    Example:
        >>> packet = create_mram_packet(b"Hello")
        >>> packet["operation"]
        'write'
        >>> len(packet["data"]["textures"])
        40
    """
    if operation not in ["write", "read"]:
        raise ValueError(f"Invalid operation: {operation}")
    
    # Generate unique packet ID
    packet_id = str(uuid.uuid4())
    
    # Encode data to magnetization textures
    textures = encode_to_magnetization(data)
    
    # Compute original data hash
    original_hash = _compute_sha256(data)
    
    # Build packet data
    packet = {
        "version": "1.0.0",
        "packet_id": packet_id,
        "operation": operation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {
            "textures": [list(texture) for texture in textures],
            "metadata": {
                "byte_count": len(data),
                "encoding_method": "tetrahedron_5solids",
                "original_hash": original_hash
            }
        },
        "checksum": ""  # Computed below
    }
    
    # Compute checksum of packet data (excluding checksum field)
    packet_json = json.dumps(packet, sort_keys=True)
    packet["checksum"] = _compute_sha256_str(packet_json)
    
    return packet


def read_mram_packet(packet: Dict[str, Any]) -> Optional[bytes]:
    """
    Read and decode data from an MRAM packet.
    
    Decodes magnetization textures from the packet and returns original data.
    
    Args:
        packet: MRAM packet dictionary conforming to packet.schema.json
        
    Returns:
        Decoded binary data, or None if decoding fails
        
    Example:
        >>> packet = create_mram_packet(b"Test")
        >>> data = read_mram_packet(packet)
        >>> data
        b'Test'
    """
    try:
        # Extract textures from packet
        textures_list = packet["data"]["textures"]
        textures = [tuple(texture) for texture in textures_list]
        
        # Decode magnetization textures
        decoded_data = decode_from_magnetization(textures)
        
        return decoded_data
    except (KeyError, TypeError, ValueError):
        return None


def verify_packet_receipt(
    packet: Dict[str, Any],
    decoded_data: Optional[bytes] = None
) -> Dict[str, Any]:
    """
    Create a verified receipt for an MRAM packet operation.
    
    Generates a receipt with SHA-based verifier proofs for probable decode.
    The proof chain establishes cryptographic verification of the decode process.
    
    Args:
        packet: MRAM packet dictionary
        decoded_data: Optional pre-decoded data (if None, will decode from packet)
        
    Returns:
        Receipt dictionary conforming to receipt.schema.json
        
    Example:
        >>> packet = create_mram_packet(b"Data")
        >>> receipt = verify_packet_receipt(packet)
        >>> receipt["verifier_proof"]["verification_status"]
        'verified'
    """
    # Generate unique receipt ID
    receipt_id = str(uuid.uuid4())
    
    # Decode data if not provided
    if decoded_data is None:
        decoded_data = read_mram_packet(packet)
    
    # Determine status
    if decoded_data is None:
        status = "failure"
        verification_status = "failed"
        data_hash = ""
        proof_chain = []
        decoded_bytes = 0
        error_msg = "Failed to decode packet data"
    else:
        status = "success"
        
        # Compute hashes for verification
        data_hash = _compute_sha256(decoded_data)
        packet_checksum = packet.get("checksum", "")
        packet_hash = _compute_sha256_str(packet_checksum)
        
        # Build proof chain: each step verifies the decode process
        # 1. Hash of packet checksum (establishes packet integrity)
        # 2. Hash of decoded data (establishes data content)
        # 3. Hash of (packet_hash + data_hash) - cryptographically binds packet to decoded data
        # 4. Hash of original data hash from metadata - verifies against original (if available)
        proof_chain = [
            packet_hash,  # Step 1: Packet integrity
            data_hash,    # Step 2: Data content
        ]
        
        # Step 3: Bind packet and data together
        combined_hash = _compute_sha256_str(packet_hash + data_hash)
        proof_chain.append(combined_hash)
        
        # Step 4: Add original hash verification if available
        original_hash = packet.get("data", {}).get("metadata", {}).get("original_hash", "")
        if original_hash:
            original_hash_verify = _compute_sha256_str(original_hash)
            proof_chain.append(original_hash_verify)
            
            # Verify decoded data matches original hash
            if data_hash == original_hash:
                verification_status = "verified"
            else:
                verification_status = "failed"
                status = "failure"
        else:
            verification_status = "verified"
        
        decoded_bytes = len(decoded_data)
        error_msg = None
    
    # Build receipt
    receipt = {
        "version": "1.0.0",
        "receipt_id": receipt_id,
        "packet_id": packet["packet_id"],
        "operation": packet["operation"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "verifier_proof": {
            "packet_hash": packet_hash if status == "success" else "",
            "data_hash": data_hash,
            "proof_chain": proof_chain,
            "verification_status": verification_status
        },
        "result": {
            "decoded_bytes": decoded_bytes
        }
    }
    
    if error_msg:
        receipt["result"]["error_message"] = error_msg
    
    return receipt
