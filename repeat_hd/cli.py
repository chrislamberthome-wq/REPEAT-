#!/usr/bin/env python3
"""Command-line interface for REPEAT-HD."""

import argparse
import sys
import struct
import zlib


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
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
