# REPEAT-

REPEAT-HD: A data encoding and verification library with CRC checksums, runtime invariant checks, and 3D geometric codec system.

## Features

- **Encode**: Encode data with CRC32 checksum for integrity verification
- **Verify**: Verify encoded data with CRC/parse checks
- **Strict Mode**: Additional runtime invariant checks for self-auditing
- **3D Codec**: Encode binary messages using geometric representations in 2D and 3D space

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

### Data Encoding and Verification

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

### 3D Codec System

The 3D codec system provides geometric encoding of binary messages. See [formulas.md](formulas.md) for detailed specifications.

```python
from repeat_hd import (
    encode_2d, decode_2d,
    encode_3d_seashell, decode_3d_seashell,
    encode_3d_solids, decode_3d_solids_rule_a
)

# 2D encoding: binary → 2D point
point = encode_2d(1)  # Returns (-1.0, 0.0)
binary = decode_2d(point)  # Returns 1

# 3D seashell encoding: binary → 3D logarithmic spiral
point = encode_3d_seashell(0)  # Returns point with negative z
binary = decode_3d_seashell(point)  # Returns 0

# 3D 5-solids encoding: binary → 5 Platonic solid angles
angles = encode_3d_solids(1)  # Returns 5 angles
binary = decode_3d_solids_rule_a(angles)  # Returns 1 via majority voting
```

Run the demonstration script to see the codec system in action:

```bash
python scripts/demo_codec.py
```
```