# CRC-16/CCITT-FALSE Reproducibility Contract

## Overview

This document defines the reproducibility rules and environmental constraints for CRC-16/CCITT-FALSE checksum calculation in this repository. All implementations MUST adhere to these rules to ensure deterministic, reproducible results across platforms, architectures, and Python versions.

## Algorithm Parameters (FROZEN)

- **Polynomial**: `0x1021`
- **Initial Value**: `0xFFFF`
- **XOR Out**: `0x0000`
- **Reflection**: None (no input or output reflection)

**These parameters are IMMUTABLE and MUST NOT be changed.**

## Input Handling

### 1. Byte Sequences
- **Primary Input Type**: All CRC calculations operate on byte sequences (`bytes` type in Python).
- **Immutability**: Input byte sequences must remain unchanged during calculation.
- **Order**: Bytes are processed in the order they appear in the sequence.

### 2. String Encoding
When calculating CRCs for text strings:
- **Default Encoding**: UTF-8 MUST be used unless explicitly specified otherwise.
- **Explicit Encoding**: Always specify encoding when converting strings to bytes.
- **Example**:
  ```python
  text = "ABC"
  data = text.encode('utf-8')  # Explicit UTF-8 encoding
  crc = crc16_ccitt_false(data)
  ```

### 3. Newline Handling
- **Platform Independence**: Newlines must be handled consistently.
- **Recommended**: Normalize newlines before CRC calculation:
  - Unix/Linux: `\n` (0x0A)
  - Windows: `\r\n` (0x0D 0x0A)
  - Classic Mac: `\r` (0x0D)
- **Best Practice**: Convert all newlines to `\n` before encoding:
  ```python
  text = text.replace('\r\n', '\n').replace('\r', '\n')
  data = text.encode('utf-8')
  ```

## Environmental Constraints

To ensure deterministic behavior across platforms, the following environment variables MUST be set during testing and certification:

### Required Environment Variables

```bash
export PYTHONHASHSEED=0    # Deterministic hash function behavior
export LC_ALL=C            # Consistent locale/collation
export TZ=UTC              # Consistent timezone
```

### Rationale

1. **PYTHONHASHSEED=0**: Ensures Python's hash() function produces consistent results across runs. While CRC calculation doesn't directly use hash(), this ensures no hidden dependencies creep in.

2. **LC_ALL=C**: Sets a consistent locale for:
   - String sorting/comparison
   - Character classification
   - Prevents locale-dependent behavior in file I/O

3. **TZ=UTC**: Ensures consistent timezone for:
   - Timestamp generation in logs/manifests
   - Prevents timezone-dependent variations

## Verification Procedure

### 1. Local Verification
```bash
# Set environment
export PYTHONHASHSEED=0
export LC_ALL=C
export TZ=UTC

# Run tests
python -m pytest tests/test_crc16_golden.py -v

# Verify manifest
make certify
```

### 2. CI Verification
The CI pipeline (`.github/workflows/certify.yml`) MUST:
- Set all required environment variables
- Run on multiple platforms: Linux, macOS, Windows
- Verify golden vectors match expected values
- Validate SHA-256 manifest checksums

### 3. Cross-Platform Testing
Results MUST be identical across:
- Operating Systems: Linux, macOS, Windows
- Python Versions: 3.8, 3.9, 3.10, 3.11, 3.12+
- Architectures: x86_64, ARM64

## Golden Vectors

Golden vectors are frozen test cases with known CRC values:

| Input | Description | CRC-16/CCITT-FALSE |
|-------|-------------|-------------------|
| `""` (empty) | Empty byte sequence | `0xFFFF` |
| `"123456789"` | ASCII digits | `0x29B1` |
| `"ABC"` | ASCII uppercase | `0xF508` |
| `00 01 02 03 04 05 06 07 08 09` | Binary sequence | `0xC241` |
| `FF × 32` | 32 bytes of 0xFF | `0x75F8` |
| `00...FF` | All 256 byte values | `0x3FBD` |

**These vectors are IMMUTABLE.** Any change to expected values requires formal review.

## Manifest Files

### 1. Vectors File: `audit/golden/crc16_ccitt_false.vectors.json`
Contains frozen input vectors with labels and expected CRC values.

### 2. Manifest File: `audit/golden/crc16_ccitt_false.manifest.json`
Contains SHA-256 checksums of:
- Golden vectors file
- Reference implementation (`tools/crc16_ccitt_false.py`)
- This documentation file

**Purpose**: Detect any unauthorized modifications to certified files.

## Certification Process

1. **Freeze Vectors**: Lock golden test vectors in JSON format
2. **Calculate CRCs**: Run reference implementation against all vectors
3. **Generate Manifest**: Calculate SHA-256 checksums of all certified files
4. **Verify CI**: Ensure CI passes on all platforms
5. **Lock Down**: Commit manifest and mark as certified baseline

## Modification Protocol

Any changes to certified files require:
1. Formal review and approval
2. Regeneration of golden vectors (if applicable)
3. Regeneration of SHA-256 manifest
4. Re-certification via CI
5. Documentation of changes in git commit message

## References

- CRC-16/CCITT-FALSE specification: [reveng.sourceforge.io](http://reveng.sourceforge.io/crc-catalogue/16.htm#crc.cat.crc-16-ccitt-false)
- Python bytes documentation: [docs.python.org/3/library/stdtypes.html#bytes](https://docs.python.org/3/library/stdtypes.html#bytes)
- UTF-8 encoding: [RFC 3629](https://tools.ietf.org/html/rfc3629)
