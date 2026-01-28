# REPEAT-

REPEAT-HD: A data encoding and verification library with CRC checksums and runtime invariant checks.

## Features

- **Encode**: Encode data with CRC32 checksum for integrity verification
- **Verify**: Verify encoded data with CRC/parse checks
- **Strict Mode**: Additional runtime invariant checks for self-auditing

## Installation

```bash
# Clone the repository
git clone https://github.com/chrislamberthome-wq/REPEAT-.git
cd REPEAT-

# Run tests
make test

# Run smoke test
make smoke
```

## Usage

### PublicHex Verification

Verify and normalize hexadecimal strings according to PublicHex v1 specification:

Using the `--hex` argument:
```bash
python -m repeat_hd.cli publichex-verify --hex "DEADBEEF"
# Output: {"encoding": "publichex-v1", "normalized_frame_hex": "deadbeef"}
# Exit code: 0 (PASS)
```

Using stdin:
```bash
echo "48 65 6C 6C 6F" | python -m repeat_hd.cli publichex-verify
# Output: {"encoding": "publichex-v1", "normalized_frame_hex": "48656c6c6f"}
# Exit code: 0 (PASS)
```

The `publichex-verify` command:
- Accepts hexadecimal input via `--hex <string>` or stdin
- Is whitespace-tolerant (removes spaces, tabs, newlines)
- Normalizes to lowercase and removes all whitespace
- Outputs JSON with `encoding` and `normalized_frame_hex` fields
- Exit codes: 0 (PASS), 2 (FAIL), 1 (parse/usage error)

### Encoding Data

```bash
python -m repeat_hd.cli encode "your data here" > output.bin
```

### Verifying Data

Basic verification (CRC and parse checks only):
```bash
python -m repeat_hd.cli verify --infile output.bin
```

Strict verification (CRC, parse, and runtime invariant checks):
```bash
python -m repeat_hd.cli verify --strict --infile output.bin
```

### The --strict Flag

The `--strict` flag enables additional runtime invariant checks that go beyond basic CRC/parse verification. These checks make the runtime self-auditing by verifying:

1. **Re-encoding consistency**: Re-encoding the decoded data produces identical output
2. **Length field accuracy**: The stored length matches the actual data length
3. **Data integrity**: No null bytes in decoded data (common corruption indicator)
4. **Size consistency**: Encoded size matches expected size (header + data)

When `--strict` is enabled:
- Exit code 0: All checks passed (CRC, parse, and invariants)
- Exit code 1: CRC or parse check failed
- Exit code 2: Invariant check failed

Without `--strict`:
- Exit code 0: CRC and parse checks passed
- Exit code 1: CRC or parse check failed

## Data Format

Encoded data format:
```
[4 bytes: CRC32][4 bytes: length][data bytes]
```

- **CRC32**: Checksum of the data bytes
- **Length**: Length of the data in bytes (little-endian)
- **Data**: UTF-8 encoded data

## Testing

```bash
# Run all tests
make test

# Run smoke test
make smoke
```

## Examples

```bash
# Encode and verify with strict mode
python -m repeat_hd.cli encode "Hello, World!" > data.bin
python -m repeat_hd.cli verify --strict --infile data.bin
# Output: VERIFICATION PASSED
#   All CRC/parse checks passed
#   All invariant checks passed

# Pipe encode to verify
python -m repeat_hd.cli encode "test data" | python -m repeat_hd.cli verify --strict
# Output: VERIFICATION PASSED
#   All CRC/parse checks passed
#   All invariant checks passed
```