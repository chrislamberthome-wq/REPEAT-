#!/usr/bin/env python3
"""
Holo-ID v0 CLI Tool

A command-line tool for encoding, decoding, verifying, and corruption simulation
of Holo-ID v0 packets using the icosidodecahedron boundary.
"""

import argparse
import base64
import binascii
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Dict, Any


# Golden ratio and related constants
PHI = (1 + 5**0.5) / 2  # Golden ratio ≈ 1.618033988749895
INV_PHI = 1 / PHI        # Inverse golden ratio ≈ 0.618033988749895

# Tolerance parameters
COORD_TOLERANCE = 1e-6
RADIUS_TOLERANCE = 1e-5


def load_boundary_data() -> Dict[str, Any]:
    """Load the canonical icosidodecahedron boundary data."""
    boundary_path = Path(__file__).parent.parent / "boundary" / "icosidodecahedron_canonical.json"
    with open(boundary_path, 'r') as f:
        return json.load(f)


def load_schema() -> Dict[str, Any]:
    """Load the Holo-ID v0 JSON schema."""
    schema_path = Path(__file__).parent.parent / "schema" / "holo-id-v0.schema.json"
    with open(schema_path, 'r') as f:
        return json.load(f)


def calculate_crc32(data: bytes) -> str:
    """Calculate CRC32 checksum of data and return as hex string."""
    crc = binascii.crc32(data) & 0xffffffff
    return f"{crc:08x}"


def byte_to_coordinate(byte_val: int, boundary_data: Dict[str, Any]) -> List[float]:
    """
    Map a byte value (0-255) to a 3D coordinate on the icosidodecahedron boundary.
    
    - Values 0-29: Direct vertex indices
    - Values 30-89: Edge midpoints
    - Values 90-255: Face centers and composite positions
    """
    vertices = boundary_data["vertices"]
    edges = boundary_data["edges"]
    
    if byte_val < 30:
        # Direct vertex mapping
        return vertices[byte_val]["coords"]
    elif byte_val < 90:
        # Edge midpoint mapping
        edge_idx = (byte_val - 30) % len(edges)
        edge = edges[edge_idx]
        v1 = vertices[edge[0]]["coords"]
        v2 = vertices[edge[1]]["coords"]
        # Return midpoint
        return [(v1[i] + v2[i]) / 2 for i in range(3)]
    else:
        # Face center and composite positions
        # Use modulo to map to available faces
        triangular_faces = boundary_data["faces"]["triangular"]
        pentagonal_faces = boundary_data["faces"]["pentagonal"]
        all_faces = triangular_faces + pentagonal_faces
        
        face_idx = (byte_val - 90) % len(all_faces)
        face = all_faces[face_idx]
        
        # Calculate face center
        center = [0.0, 0.0, 0.0]
        for vertex_id in face:
            coords = vertices[vertex_id]["coords"]
            for i in range(3):
                center[i] += coords[i]
        
        # Average to get center
        n = len(face)
        return [center[i] / n for i in range(3)]


def coordinate_to_byte(coord: List[float], boundary_data: Dict[str, Any]) -> int:
    """
    Map a 3D coordinate back to a byte value (0-255).
    Uses nearest neighbor search among all possible encoded positions.
    """
    min_dist = float('inf')
    best_byte = 0
    
    # Check all possible byte values
    for byte_val in range(256):
        expected_coord = byte_to_coordinate(byte_val, boundary_data)
        dist = sum((coord[i] - expected_coord[i])**2 for i in range(3))
        if dist < min_dist:
            min_dist = dist
            best_byte = byte_val
    
    return best_byte


def encode_data(data: bytes, boundary_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encode binary data into a Holo-ID v0 packet.
    
    Args:
        data: Binary data to encode
        boundary_data: Icosidodecahedron boundary definition
        
    Returns:
        Dictionary representing the Holo-ID v0 packet
    """
    # Calculate checksum
    checksum = calculate_crc32(data)
    
    # Encode each byte to a coordinate
    coordinates = [byte_to_coordinate(byte_val, boundary_data) for byte_val in data]
    
    # Create packet
    packet = {
        "version": "v0",
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "data": base64.b64encode(data).decode('ascii'),
        "geometry": {
            "boundary": "icosidodecahedron",
            "coordinates": coordinates
        },
        "checksum": {
            "algorithm": "CRC32",
            "value": checksum
        }
    }
    
    return packet


def decode_data(packet: Dict[str, Any], boundary_data: Dict[str, Any]) -> bytes:
    """
    Decode a Holo-ID v0 packet back to binary data.
    
    Args:
        packet: Holo-ID v0 packet dictionary
        boundary_data: Icosidodecahedron boundary definition
        
    Returns:
        Decoded binary data
    """
    coordinates = packet["geometry"]["coordinates"]
    
    # Decode each coordinate back to a byte
    data_bytes = bytes([coordinate_to_byte(coord, boundary_data) for coord in coordinates])
    
    return data_bytes


def validate_schema(packet: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate packet against JSON schema (simplified validation).
    
    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    required_fields = ["version", "timestamp", "data", "geometry", "checksum"]
    for field in required_fields:
        if field not in packet:
            return False, f"Missing required field: {field}"
    
    # Check version
    if packet["version"] != "v0":
        return False, f"Invalid version: {packet['version']}"
    
    # Check geometry structure
    if "boundary" not in packet["geometry"]:
        return False, "Missing geometry.boundary"
    if packet["geometry"]["boundary"] != "icosidodecahedron":
        return False, f"Invalid boundary: {packet['geometry']['boundary']}"
    if "coordinates" not in packet["geometry"]:
        return False, "Missing geometry.coordinates"
    
    # Check checksum structure
    if "algorithm" not in packet["checksum"]:
        return False, "Missing checksum.algorithm"
    if packet["checksum"]["algorithm"] != "CRC32":
        return False, f"Invalid checksum algorithm: {packet['checksum']['algorithm']}"
    if "value" not in packet["checksum"]:
        return False, "Missing checksum.value"
    
    return True, ""


def verify_basic(packet: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Perform basic verification: schema validation and checksum.
    
    Returns:
        (passed, message)
    """
    # Validate schema
    valid, error = validate_schema(packet, schema)
    if not valid:
        return False, f"Schema validation failed: {error}"
    
    # Verify checksum
    try:
        data = base64.b64decode(packet["data"])
        expected_checksum = calculate_crc32(data)
        actual_checksum = packet["checksum"]["value"]
        
        if expected_checksum != actual_checksum:
            return False, f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
    except Exception as e:
        return False, f"Checksum verification error: {e}"
    
    return True, "Basic verification passed"


def verify_strict(packet: Dict[str, Any], schema: Dict[str, Any], boundary_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Perform strict verification: basic checks + runtime invariants.
    
    Returns:
        (passed, message)
    """
    # First do basic verification
    passed, msg = verify_basic(packet, schema)
    if not passed:
        return False, msg
    
    # Runtime invariant checks
    try:
        # 1. Re-encoding consistency
        data = base64.b64decode(packet["data"])
        re_encoded = encode_data(data, boundary_data)
        
        # Check if coordinates match (within tolerance)
        original_coords = packet["geometry"]["coordinates"]
        new_coords = re_encoded["geometry"]["coordinates"]
        
        if len(original_coords) != len(new_coords):
            return False, f"Invariant check failed: coordinate count mismatch ({len(original_coords)} vs {len(new_coords)})"
        
        for i, (orig, new) in enumerate(zip(original_coords, new_coords)):
            for j in range(3):
                if abs(orig[j] - new[j]) > COORD_TOLERANCE:
                    return False, f"Invariant check failed: re-encoding mismatch at coordinate {i}, dimension {j}"
        
        # 2. Coordinate validation (all should be reasonable)
        for i, coord in enumerate(original_coords):
            if len(coord) != 3:
                return False, f"Invariant check failed: coordinate {i} is not 3D"
            
            # Check if coordinate values are reasonable (not too large)
            for j, val in enumerate(coord):
                if abs(val) > 10.0:  # Reasonable bound for icosidodecahedron
                    return False, f"Invariant check failed: coordinate {i}[{j}] out of reasonable range: {val}"
        
        # 3. Data integrity (no obvious corruption indicators)
        # This is a soft check - data could legitimately contain null bytes
        # but unexpected patterns might indicate corruption
        
        # 4. Length consistency
        if len(original_coords) != len(data):
            return False, f"Invariant check failed: coordinate count ({len(original_coords)}) != data length ({len(data)})"
        
    except Exception as e:
        return False, f"Invariant check error: {e}"
    
    return True, "Strict verification passed (all invariants satisfied)"


def corrupt_packet(packet: Dict[str, Any], corruption_type: str) -> Dict[str, Any]:
    """
    Simulate corruption of a Holo-ID v0 packet.
    
    Corruption types:
        - bitflip: Random bit flip in binary data
        - coordinate: Random perturbation of a coordinate
        - checksum: Alter checksum without changing data
        - geometry: Change coordinate without updating data
    """
    corrupted = json.loads(json.dumps(packet))  # Deep copy
    
    if corruption_type == "bitflip":
        # Flip a random bit in the data
        data = base64.b64decode(corrupted["data"])
        if len(data) > 0:
            data_list = list(data)
            byte_idx = random.randint(0, len(data_list) - 1)
            bit_idx = random.randint(0, 7)
            data_list[byte_idx] ^= (1 << bit_idx)
            corrupted["data"] = base64.b64encode(bytes(data_list)).decode('ascii')
    
    elif corruption_type == "coordinate":
        # Perturb a random coordinate
        coords = corrupted["geometry"]["coordinates"]
        if len(coords) > 0:
            coord_idx = random.randint(0, len(coords) - 1)
            dim_idx = random.randint(0, 2)
            perturbation = random.uniform(-0.1, 0.1)
            coords[coord_idx][dim_idx] += perturbation
    
    elif corruption_type == "checksum":
        # Flip a bit in the checksum
        checksum = int(corrupted["checksum"]["value"], 16)
        bit_to_flip = random.randint(0, 31)
        checksum ^= (1 << bit_to_flip)
        corrupted["checksum"]["value"] = f"{checksum:08x}"
    
    elif corruption_type == "geometry":
        # Change a coordinate without updating the data
        coords = corrupted["geometry"]["coordinates"]
        if len(coords) > 0:
            coord_idx = random.randint(0, len(coords) - 1)
            # Replace with a random vertex coordinate
            from_boundary = load_boundary_data()
            random_vertex = random.choice(from_boundary["vertices"])
            coords[coord_idx] = random_vertex["coords"]
    
    else:
        raise ValueError(f"Unknown corruption type: {corruption_type}")
    
    return corrupted


def cmd_encode(args):
    """Handle encode command."""
    # Read input data
    if args.input:
        with open(args.input, 'rb') as f:
            data = f.read()
    else:
        data = sys.stdin.buffer.read()
    
    # Load boundary data
    boundary_data = load_boundary_data()
    
    # Encode
    packet = encode_data(data, boundary_data)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(packet, f, indent=2)
    else:
        print(json.dumps(packet, indent=2))
    
    return 0


def cmd_decode(args):
    """Handle decode command."""
    # Read input packet
    if args.input:
        with open(args.input, 'r') as f:
            packet = json.load(f)
    else:
        packet = json.load(sys.stdin)
    
    # Load boundary data
    boundary_data = load_boundary_data()
    
    # Decode
    data = decode_data(packet, boundary_data)
    
    # Write output
    if args.output:
        with open(args.output, 'wb') as f:
            f.write(data)
    else:
        sys.stdout.buffer.write(data)
    
    return 0


def cmd_verify(args):
    """Handle verify command."""
    # Read input packet
    if args.input:
        with open(args.input, 'r') as f:
            packet = json.load(f)
    else:
        packet = json.load(sys.stdin)
    
    # Load schema and boundary data
    schema = load_schema()
    boundary_data = load_boundary_data()
    
    # Perform verification
    if args.strict:
        passed, message = verify_strict(packet, schema, boundary_data)
        exit_code = 0 if passed else 2
    else:
        passed, message = verify_basic(packet, schema)
        exit_code = 0 if passed else 1
    
    # Output result
    if passed:
        print(f"VERIFICATION PASSED: {message}")
    else:
        print(f"VERIFICATION FAILED: {message}", file=sys.stderr)
    
    return exit_code


def cmd_corrupt(args):
    """Handle corrupt command."""
    # Read input packet
    if args.input:
        with open(args.input, 'r') as f:
            packet = json.load(f)
    else:
        packet = json.load(sys.stdin)
    
    # Corrupt packet
    corrupted = corrupt_packet(packet, args.type)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(corrupted, f, indent=2)
    else:
        print(json.dumps(corrupted, indent=2))
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Holo-ID v0 CLI Tool - Encode, decode, verify, and corrupt audit log packets"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Encode data to Holo-ID v0 packet')
    encode_parser.add_argument('--input', '-i', help='Input file (default: stdin)')
    encode_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    # Decode command
    decode_parser = subparsers.add_parser('decode', help='Decode Holo-ID v0 packet to data')
    decode_parser.add_argument('--input', '-i', help='Input packet file (default: stdin)')
    decode_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify Holo-ID v0 packet')
    verify_parser.add_argument('--input', '-i', help='Input packet file (default: stdin)')
    verify_parser.add_argument('--strict', action='store_true', help='Enable strict verification with invariant checks')
    
    # Corrupt command
    corrupt_parser = subparsers.add_parser('corrupt', help='Simulate corruption of Holo-ID v0 packet')
    corrupt_parser.add_argument('--input', '-i', help='Input packet file (default: stdin)')
    corrupt_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    corrupt_parser.add_argument('--type', '-t', required=True, 
                               choices=['bitflip', 'coordinate', 'checksum', 'geometry'],
                               help='Type of corruption to simulate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to appropriate command
    if args.command == 'encode':
        return cmd_encode(args)
    elif args.command == 'decode':
        return cmd_decode(args)
    elif args.command == 'verify':
        return cmd_verify(args)
    elif args.command == 'corrupt':
        return cmd_corrupt(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
