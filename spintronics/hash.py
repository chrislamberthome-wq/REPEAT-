"""Hashing utilities for spintronics receipts and traces.

This module provides cryptographic hashing for experimental packets,
receipts, and pulse traces to ensure data integrity.
"""

import hashlib
import json
from typing import Dict, Any, List
from .canonical import canonicalize_json


def hash_packet(packet: Dict[str, Any], algorithm: str = 'sha256') -> str:
    """
    Compute cryptographic hash of a packet.
    
    Uses canonical JSON representation to ensure consistent hashing.
    
    Args:
        packet: Packet dictionary to hash
        algorithm: Hash algorithm to use ('sha256', 'md5', 'sha1')
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        ValueError: If algorithm is not supported
        
    Example:
        >>> packet = {"id": "test", "data": [1, 2, 3]}
        >>> hash_packet(packet)[:8]  # First 8 chars
        'a7c5e...'
    """
    if algorithm not in ['sha256', 'md5', 'sha1']:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")
    
    # Canonicalize JSON for consistent hashing
    canonical = canonicalize_json(packet)
    
    # Compute hash
    hasher = hashlib.new(algorithm)
    hasher.update(canonical.encode('utf-8'))
    
    return hasher.hexdigest()


def hash_trace(pulse_sequence: List[Dict[str, Any]], algorithm: str = 'sha256') -> str:
    """
    Compute hash of a pulse trace sequence.
    
    Args:
        pulse_sequence: List of pulse dictionaries
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal hash string
        
    Example:
        >>> pulses = [{"index": 0, "amplitude": 1.0}, {"index": 1, "amplitude": 2.0}]
        >>> hash_trace(pulses)[:8]
        'b3f2a...'
    """
    # Create canonical representation of pulse sequence
    trace_data = {"pulse_sequence": pulse_sequence}
    return hash_packet(trace_data, algorithm)


def compute_receipt_hash(write_op: Dict[str, Any], read_op: Dict[str, Any]) -> str:
    """
    Compute receipt hash from write and read operations.
    
    Creates a canonical representation of the MRAM write/read cycle
    and computes its SHA-256 hash.
    
    Args:
        write_op: Write operation dictionary
        read_op: Read operation dictionary
        
    Returns:
        SHA-256 hexadecimal hash string
        
    Example:
        >>> write = {"address": "0x100", "data_bit": 1}
        >>> read = {"resistance_state": 1000.0, "decoded_bit": 1}
        >>> compute_receipt_hash(write, read)[:8]
        'c4d8f...'
    """
    receipt_data = {
        "write_operation": write_op,
        "read_operation": read_op
    }
    return hash_packet(receipt_data, 'sha256')


def verify_checksum(data: Dict[str, Any], expected_checksum: str, 
                    algorithm: str = 'sha256') -> bool:
    """
    Verify that data matches expected checksum.
    
    Args:
        data: Data dictionary to verify
        expected_checksum: Expected hash value (hexadecimal)
        algorithm: Hash algorithm used
        
    Returns:
        True if checksums match, False otherwise
        
    Example:
        >>> data = {"value": 42}
        >>> checksum = hash_packet(data)
        >>> verify_checksum(data, checksum)
        True
    """
    computed = hash_packet(data, algorithm)
    return computed == expected_checksum
