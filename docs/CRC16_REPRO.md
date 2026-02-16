# CRC-16 CCITT-False Reproducibility Guide

This document provides guidance for reproducing CRC-16 CCITT-False calculations using the CLI tool, with emphasis on avoiding common pitfalls related to trailing newlines.

## Overview

The `tools/crc16_ccitt_false.py` script calculates CRC-16 checksums using the CCITT-False polynomial (0x1021) with:
- Initial value: 0xFFFF
- No input reflection
- No output reflection  
- No final XOR (0x0000)

## Usage Examples

### Correct: Using `printf` (Recommended)

The `printf` command does NOT add a trailing newline by default, making it the most reliable choice:

```bash
# Correct: no trailing newline
printf "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py

# Another example
printf "test data" | python3 tools/crc16_ccitt_false.py
```

### Alternative: Using `echo -n` (Platform-Specific)

The `echo -n` flag suppresses the trailing newline, but behavior may vary across shells:

```bash
# Still valid (but platform-specific)
echo -n "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
```

### Command-Line Argument

You can also pass the data directly as a command-line argument:

```bash
python3 tools/crc16_ccitt_false.py "F0|ABC|3|1"
```

## Common Pitfalls

### ❌ Avoid: Plain `echo` (Adds Trailing Newline)

```bash
# INCORRECT - adds '\n' which changes the CRC
echo "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
```

The plain `echo` command appends a newline character (`\n`), which will be included in the CRC calculation and produce a different result.

## Golden Test Vector

The following test vector can be used to verify correct implementation:

```bash
printf "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
# Expected output: 0x34B6
```

## Implementation Notes

- The tool reads from stdin in binary mode to avoid platform-specific line ending conversions
- Input is processed as UTF-8 encoded bytes
- The output is a hexadecimal string in the format `0xXXXX`
