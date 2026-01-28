#!/usr/bin/env python3
"""Command-line interface for REPEAT-HD."""

import argparse
import sys
import struct
import zlib
import json
import re


def encode_data(data: str) -> bytes:
    """
    Encode data with CRC checksum.
    
    Format: [4 bytes: CRC32][4 bytes: length][data bytes]
    """
    data_bytes = data.encode('utf-8')
    length = len(data_bytes)
    
    # Calculate CRC32 of the data
    crc = zlib.crc32(data_bytes) & 0xffffffff
    
    # Pack: CRC (4 bytes), length (4 bytes), then data
    encoded = struct.pack('<II', crc, length) + data_bytes
    
    return encoded


def decode_data(encoded: bytes) -> tuple[str, bool, list[str]]:
    """
    Decode data and verify CRC checksum.
    
    Returns:
        tuple: (decoded_string, is_valid, errors)
            - decoded_string: The decoded data (empty if invalid)
            - is_valid: True if CRC and parsing succeeded
            - errors: List of error messages
    """
    errors = []
    
    # Check minimum size
    if len(encoded) < 8:
        errors.append("Data too short: minimum 8 bytes required")
        return "", False, errors
    
    try:
        # Unpack header
        stored_crc, length = struct.unpack('<II', encoded[:8])
        data_bytes = encoded[8:]
        
        # Check if data length matches
        if len(data_bytes) != length:
            errors.append(f"Length mismatch: expected {length}, got {len(data_bytes)}")
            return "", False, errors
        
        # Verify CRC
        calculated_crc = zlib.crc32(data_bytes) & 0xffffffff
        if stored_crc != calculated_crc:
            errors.append(f"CRC mismatch: expected {stored_crc:08x}, got {calculated_crc:08x}")
            return "", False, errors
        
        # Decode data
        decoded = data_bytes.decode('utf-8')
        
        return decoded, True, errors
        
    except struct.error as e:
        errors.append(f"Parse error: {e}")
        return "", False, errors
    except UnicodeDecodeError as e:
        errors.append(f"UTF-8 decode error: {e}")
        return "", False, errors


def check_invariants(data: str, encoded: bytes) -> list[str]:
    """
    Perform runtime invariant checks on encoded data.
    
    These checks ensure internal consistency and correctness beyond
    basic CRC/parse verification.
    
    Returns:
        list: Error messages for any violations found
    """
    violations = []
    
    # Invariant 1: Re-encoding should produce identical output
    re_encoded = encode_data(data)
    if re_encoded != encoded:
        violations.append("Invariant violation: re-encoding produces different output")
    
    # Invariant 2: Length field should match actual data length
    if len(encoded) >= 8:
        _, stored_length = struct.unpack('<II', encoded[:8])
        actual_data_length = len(encoded) - 8
        if stored_length != actual_data_length:
            violations.append(
                f"Invariant violation: stored length ({stored_length}) != "
                f"actual data length ({actual_data_length})"
            )
    
    # Invariant 3: Data should not contain null bytes (common corruption indicator)
    if '\x00' in data:
        violations.append("Invariant violation: decoded data contains null bytes")
    
    # Invariant 4: Encoded size should be reasonable (header + data)
    expected_size = 8 + len(data.encode('utf-8'))
    if len(encoded) != expected_size:
        violations.append(
            f"Invariant violation: encoded size ({len(encoded)}) != "
            f"expected size ({expected_size})"
        )
    
    return violations


def cmd_encode(args):
    """Handle the encode command."""
    data = args.data
    encoded = encode_data(data)
    
    # Write binary output to stdout
    sys.stdout.buffer.write(encoded)
    return 0


def cmd_verify(args):
    """Handle the verify command."""
    # Read input
    if args.infile:
        with open(args.infile, 'rb') as f:
            encoded = f.read()
    else:
        encoded = sys.stdin.buffer.read()
    
    # Decode and verify CRC/parse
    decoded, is_valid, errors = decode_data(encoded)
    
    if not is_valid:
        print("VERIFICATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    
    # If --strict flag is enabled, perform additional invariant checks
    if args.strict:
        violations = check_invariants(decoded, encoded)
        if violations:
            print("STRICT MODE VIOLATIONS DETECTED", file=sys.stderr)
            for violation in violations:
                print(f"  - {violation}", file=sys.stderr)
            return 2
    
    # Success
    print("VERIFICATION PASSED", file=sys.stderr)
    if args.strict:
        print("  All CRC/parse checks passed", file=sys.stderr)
        print("  All invariant checks passed", file=sys.stderr)
    else:
        print("  All CRC/parse checks passed", file=sys.stderr)
    
    return 0


def normalize_hex(hex_input: str) -> tuple[str, list[str]]:
    """
    Normalize hex string by removing whitespace and converting to lowercase.
    
    Args:
        hex_input: Input hex string (may contain whitespace)
        
    Returns:
        tuple: (normalized_hex, errors)
            - normalized_hex: Lowercase hex without whitespace
            - errors: List of validation error messages
    """
    errors = []
    
    # Remove all whitespace
    normalized = re.sub(r'\s+', '', hex_input)
    
    # Convert to lowercase
    normalized = normalized.lower()
    
    # Validate hex characters
    if not re.match(r'^[0-9a-f]*$', normalized):
        invalid_chars = set(c for c in normalized if c not in '0123456789abcdef')
        errors.append(f"Invalid hex characters found: {', '.join(sorted(invalid_chars))}")
        return "", errors
    
    return normalized, errors


def verify_publichex_frame(hex_string: str) -> tuple[bool, list[str]]:
    """
    Verify a PublicHex frame.
    
    Args:
        hex_string: Normalized hex string (lowercase, no whitespace)
        
    Returns:
        tuple: (is_valid, errors)
            - is_valid: True if frame is valid
            - errors: List of validation error messages
    """
    errors = []
    
    # Check minimum length (8 bytes = 16 hex chars for header)
    if len(hex_string) < 16:
        errors.append(f"Frame too short: minimum 16 hex characters required, got {len(hex_string)}")
        return False, errors
    
    # Check even number of hex characters
    if len(hex_string) % 2 != 0:
        errors.append("Invalid hex string: odd number of characters")
        return False, errors
    
    # Convert hex to bytes
    try:
        frame_bytes = bytes.fromhex(hex_string)
    except ValueError as e:
        errors.append(f"Failed to decode hex: {e}")
        return False, errors
    
    # Use existing decode_data function to verify the frame
    decoded, is_valid, decode_errors = decode_data(frame_bytes)
    
    if not is_valid:
        errors.extend(decode_errors)
        return False, errors
    
    return True, errors


def cmd_publichex_verify(args):
    """Handle the publichex-verify command."""
    # Get input
    if args.hex:
        hex_input = args.hex
    else:
        # Read from stdin
        hex_input = sys.stdin.read()
    
    # Normalize the hex input
    normalized_hex, norm_errors = normalize_hex(hex_input)
    
    if norm_errors:
        # Parse/usage error
        print(json.dumps({
            "encoding": "publichex-v1",
            "normalized_frame_hex": "",
            "errors": norm_errors
        }), file=sys.stderr)
        return 1
    
    # Verify the frame
    is_valid, verify_errors = verify_publichex_frame(normalized_hex)
    
    # Always output the normalized hex in JSON
    output = {
        "encoding": "publichex-v1",
        "normalized_frame_hex": normalized_hex
    }
    
    print(json.dumps(output))
    
    if not is_valid:
        # FAIL - frame parsed but validation failed
        print(json.dumps({"errors": verify_errors}), file=sys.stderr)
        return 2
    
    # PASS
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='repeat_hd',
        description='REPEAT-HD: Data encoding and verification tool'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Encode command
    encode_parser = subparsers.add_parser(
        'encode',
        help='Encode data with CRC checksum'
    )
    encode_parser.add_argument(
        'data',
        help='Data to encode'
    )
    encode_parser.set_defaults(func=cmd_encode)
    
    # Verify command
    verify_parser = subparsers.add_parser(
        'verify',
        help='Verify encoded data integrity'
    )
    verify_parser.add_argument(
        '--infile',
        help='Input file to verify (reads from stdin if not specified)'
    )
    verify_parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable additional runtime invariant checks for enhanced data '
             'integrity verification beyond basic CRC/parse checks.'
    )
    verify_parser.set_defaults(func=cmd_verify)
    
    # PublicHex verify command
    publichex_parser = subparsers.add_parser(
        'publichex-verify',
        help='Verify PublicHex v1 encoded frames'
    )
    publichex_parser.add_argument(
        '--hex',
        help='Hex string to verify (reads from stdin if not specified)'
    )
    publichex_parser.set_defaults(func=cmd_publichex_verify)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
