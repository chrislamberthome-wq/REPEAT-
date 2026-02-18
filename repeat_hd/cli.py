#!/usr/bin/env python3
"""Command-line interface for REPEAT-HD."""

import argparse
import sys
import struct
import zlib
from typing import Optional


class B4IULockedCounter:
    """
    Before-In-Use (B4IU) locked counter for tracking verification operations.
    
    This counter enforces a "spec rule" that verification operations must
    follow proper ordering and constraints before data can be considered safe
    for use. Once locked, the counter becomes immutable.
    """
    
    def __init__(self):
        """Initialize the B4IU counter."""
        self._count = 0
        self._locked = False
        self._violations = []
    
    def increment(self) -> bool:
        """
        Increment the counter if not locked.
        
        Returns:
            bool: True if increment succeeded, False if locked
        """
        if self._locked:
            self._violations.append("Attempted to increment locked counter")
            return False
        self._count += 1
        return True
    
    def lock(self) -> None:
        """Lock the counter, making it immutable."""
        self._locked = True
    
    def is_locked(self) -> bool:
        """Check if the counter is locked."""
        return self._locked
    
    def get_count(self) -> int:
        """Get the current count."""
        return self._count
    
    def get_violations(self) -> list[str]:
        """Get list of spec rule violations."""
        return self._violations.copy()
    
    def check_spec_rule(self, min_required: int = 1) -> tuple[bool, Optional[str]]:
        """
        Check if the counter meets the spec rule requirements.
        
        Spec Rule: Counter must have been incremented at least min_required
        times before being locked.
        
        Args:
            min_required: Minimum required count before locking (default: 1)
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if self._locked and self._count < min_required:
            return False, f"Spec rule violation: counter locked with count={self._count}, required>={min_required}"
        return True, None


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
    """Handle the verify command with b4iu locked counter tracking."""
    # Initialize B4IU counter for this verification operation
    b4iu_counter = B4IULockedCounter()
    
    # Read input
    if args.infile:
        with open(args.infile, 'rb') as f:
            encoded = f.read()
    else:
        encoded = sys.stdin.buffer.read()
    
    # Track that we've started verification
    b4iu_counter.increment()
    
    # Decode and verify CRC/parse
    decoded, is_valid, errors = decode_data(encoded)
    
    if not is_valid:
        print("VERIFICATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        # Lock counter before returning (verification complete but failed)
        b4iu_counter.lock()
        # Check spec rule compliance
        spec_valid, spec_error = b4iu_counter.check_spec_rule()
        if not spec_valid:
            print(f"  - {spec_error}", file=sys.stderr)
        return 1
    
    # If --strict flag is enabled, perform additional invariant checks
    if args.strict:
        # Increment counter for strict mode checks
        b4iu_counter.increment()
        
        violations = check_invariants(decoded, encoded)
        if violations:
            print("STRICT MODE VIOLATIONS DETECTED", file=sys.stderr)
            for violation in violations:
                print(f"  - {violation}", file=sys.stderr)
            # Lock counter before returning
            b4iu_counter.lock()
            # Check spec rule compliance
            spec_valid, spec_error = b4iu_counter.check_spec_rule(min_required=2)
            if not spec_valid:
                print(f"  - {spec_error}", file=sys.stderr)
            return 2
    
    # Lock counter after successful verification
    b4iu_counter.lock()
    
    # Check spec rule compliance
    spec_valid, spec_error = b4iu_counter.check_spec_rule(min_required=2 if args.strict else 1)
    
    # Success
    print("VERIFICATION PASSED", file=sys.stderr)
    if args.strict:
        print("  All CRC/parse checks passed", file=sys.stderr)
        print("  All invariant checks passed", file=sys.stderr)
        print(f"  B4IU counter: {b4iu_counter.get_count()} operations tracked", file=sys.stderr)
    else:
        print("  All CRC/parse checks passed", file=sys.stderr)
        print(f"  B4IU counter: {b4iu_counter.get_count()} operations tracked", file=sys.stderr)
    
    # Report spec rule status
    if not spec_valid:
        print(f"  Warning: {spec_error}", file=sys.stderr)
    
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
