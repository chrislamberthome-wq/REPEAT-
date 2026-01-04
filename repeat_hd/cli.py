"""CLI module for REPEAT-HD encoding and verification."""

import sys
import hashlib


def encode(text):
    """Encode text and output with checksum."""
    checksum = hashlib.sha256(text.encode()).hexdigest()
    return f"{text}:{checksum}"


def verify(encoded_text):
    """Verify encoded text with checksum."""
    if ':' not in encoded_text:
        return False
    text, expected_checksum = encoded_text.rsplit(':', 1)
    actual_checksum = hashlib.sha256(text.encode()).hexdigest()
    return actual_checksum == expected_checksum


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m repeat_hd.cli {encode|verify} [text]", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "encode":
        if len(sys.argv) < 3:
            print("Usage: python -m repeat_hd.cli encode <text>", file=sys.stderr)
            sys.exit(1)
        text = sys.argv[2]
        encoded = encode(text)
        print(encoded)
    
    elif command == "verify":
        # Read from stdin if no text provided
        if len(sys.argv) >= 3:
            encoded_text = sys.argv[2]
        else:
            encoded_text = sys.stdin.read().strip()
        
        if verify(encoded_text):
            print("Verification successful", file=sys.stderr)
            sys.exit(0)
        else:
            print("Verification failed", file=sys.stderr)
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
