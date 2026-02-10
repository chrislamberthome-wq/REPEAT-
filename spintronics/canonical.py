"""JSON canonicalization utilities for spintronics packets.

This module provides JSON canonicalization to ensure consistent
representation of spintronics experimental data.
"""

import json
from typing import Any, Dict


def canonicalize_json(data: Dict[str, Any]) -> str:
    """
    Canonicalize JSON data for consistent representation.
    
    Ensures consistent key ordering and formatting for hashing and comparison.
    Uses deterministic serialization with sorted keys and no whitespace.
    
    Args:
        data: Dictionary to canonicalize
        
    Returns:
        Canonical JSON string representation
        
    Example:
        >>> data = {"b": 2, "a": 1}
        >>> canonicalize_json(data)
        '{"a":1,"b":2}'
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def validate_canonical_form(json_str: str) -> bool:
    """
    Validate that a JSON string is in canonical form.
    
    Checks if the JSON string matches its canonical representation.
    
    Args:
        json_str: JSON string to validate
        
    Returns:
        True if string is in canonical form, False otherwise
        
    Example:
        >>> validate_canonical_form('{"a":1,"b":2}')
        True
        >>> validate_canonical_form('{"b": 2, "a": 1}')
        False
    """
    try:
        data = json.loads(json_str)
        canonical = canonicalize_json(data)
        return json_str == canonical
    except (json.JSONDecodeError, TypeError):
        return False


def normalize_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a packet by round-tripping through canonical form.
    
    Useful for ensuring consistent packet structure before hashing or storage.
    
    Args:
        packet: Packet dictionary to normalize
        
    Returns:
        Normalized packet dictionary with sorted keys
        
    Example:
        >>> packet = {"timestamp": "2024-01-01", "id": "abc"}
        >>> norm = normalize_packet(packet)
        >>> list(norm.keys())
        ['id', 'timestamp']
    """
    canonical_str = canonicalize_json(packet)
    return json.loads(canonical_str)
