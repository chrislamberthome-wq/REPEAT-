# CRC-16/CCITT-FALSE Reproduction Guide

This document provides usage examples for the CRC-16/CCITT-FALSE implementation and demonstrates how to independently verify results.

## Overview

The `tools/crc16_ccitt_false.py` script implements the CRC-16/CCITT-FALSE algorithm with the following parameters:

- **Polynomial**: 0x1021
- **Initial value**: 0xFFFF
- **Final XOR**: 0x0000
- **Reflect input**: False
- **Reflect output**: False

## Usage

### Command-line with --payload

Calculate CRC for a string directly:

```bash
python3 tools/crc16_ccitt_false.py --payload "F0|ABC|3|1"
# Output: 34B6
```

### Standard input (stdin)

Calculate CRC from stdin:

```bash
echo -n "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
# Output: 34B6

printf "ever" | python3 tools/crc16_ccitt_false.py
# Output: A1F5
```

### From files

Calculate CRC of file contents:

```bash
cat file.txt | python3 tools/crc16_ccitt_false.py
```

## Golden Vector

The implementation is validated against the golden vector:

- **Input**: `F0|ABC|3|1` (ASCII string)
- **Expected CRC**: `34B6`

This can be verified with:

```bash
echo -n "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
```

## Independent Verification

You can independently verify the CRC results using various methods:

### Using Python directly

```python
from tools.crc16_ccitt_false import crc16_ccitt_false

# Calculate CRC
data = b'F0|ABC|3|1'
crc = crc16_ccitt_false(data)
print(f"{crc:04X}")  # Output: 34B6
```

### Using printf with binary data

```bash
# Test with ASCII string
printf "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py

# Test with raw bytes (if needed)
printf "\xF0\xAB\xC3\x01" | python3 tools/crc16_ccitt_false.py
```

### Using online CRC calculators

Many online CRC calculators support CRC-16/CCITT-FALSE. Ensure the calculator uses:
- Polynomial: 0x1021
- Initial: 0xFFFF
- Final XOR: 0x0000
- Input/Output not reflected

## Output Format

The tool always outputs the CRC in:
- **Uppercase** hexadecimal
- **Zero-padded** to 4 digits (e.g., `34B6`, `00FF`, `FFFF`)

## Testing

Run the test suite to verify the implementation:

```bash
# Test golden vector
python -m pytest tests/test_crc16_golden.py -v

# Test CLI behavior
python -m pytest tests/test_crc16_cli_parity.py -v

# Run all CRC tests
python -m pytest tests/test_crc16*.py -v
```

## Integration

The CRC-16/CCITT-FALSE tool is integrated into the CI workflow and runs automatically on all pushes and pull requests to ensure correctness across different Python versions and operating systems.
