# CRC-16/CCITT-FALSE Certification System

This directory contains the frozen golden vectors and cryptographic manifest for the CRC-16/CCITT-FALSE baseline certification.

## Purpose

The certification system ensures:
- **Reproducibility**: CRC calculations are deterministic across all platforms
- **Immutability**: Certified files cannot be modified without detection
- **Verification**: SHA-256 checksums provide cryptographic proof of integrity

## Files

### Golden Vectors
- **`crc16_ccitt_false.vectors.json`**: Frozen test vectors with known CRC values
  - 6 golden test cases covering edge cases and standard inputs
  - Includes empty strings, ASCII text, and binary sequences
  - IMMUTABLE - any change requires formal review and re-certification

### Manifest
- **`crc16_ccitt_false.manifest.json`**: SHA-256 checksums of certified files
  - Reference implementation: `tools/crc16_ccitt_false.py`
  - Golden vectors: `audit/golden/crc16_ccitt_false.vectors.json`
  - Documentation: `docs/CRC16_REPRO.md`

## Usage

### Verify Certification
```bash
make verify-manifest
```

### Generate New Manifest (after approved changes)
```bash
make certify
```

This will:
1. Validate golden vectors file
2. Generate new SHA-256 manifest
3. Verify the manifest
4. Run all certification tests

### Run Tests Only
```bash
make test
```

## Certification Process

1. **Initial Certification**: Freeze golden vectors and generate manifest
2. **Continuous Verification**: CI checks manifest on every PR
3. **Re-Certification**: Required after any change to certified files

## Modification Protocol

Changes to certified files require:
1. Formal review and approval
2. Regeneration of manifest: `make certify`
3. Re-verification via CI
4. Documentation in commit message

## CI Integration

The `.github/workflows/certify.yml` workflow:
- Runs on Linux, macOS, and Windows
- Verifies manifest integrity
- Runs golden vector tests
- Checks cross-platform determinism

## Algorithm Parameters (FROZEN)

- **Polynomial**: 0x1021
- **Initial Value**: 0xFFFF
- **XOR Out**: 0x0000
- **Reflection**: None

These parameters are immutable and must not be changed.

## Golden Test Vectors

| Label | Input | Expected CRC |
|-------|-------|--------------|
| empty | `""` | 0xFFFF |
| numeric_123456789 | `"123456789"` | 0x29B1 |
| text_abc | `"ABC"` | 0xF508 |
| binary_00_to_09 | `0x00..0x09` | 0xC241 |
| binary_ff_x32 | `0xFF × 32` | 0x75F8 |
| binary_00_to_ff | `0x00..0xFF` | 0x3FBD |

## Security

The SHA-256 manifest provides cryptographic assurance that:
- No silent modifications have occurred
- All certified files are authentic
- The certification baseline is intact

Any checksum mismatch indicates:
- Unauthorized modification
- File corruption
- Need for re-certification

## References

- [CRC-16/CCITT-FALSE Specification](http://reveng.sourceforge.io/crc-catalogue/16.htm#crc.cat.crc-16-ccitt-false)
- [Reproducibility Documentation](../../docs/CRC16_REPRO.md)
- [Reference Implementation](../../tools/crc16_ccitt_false.py)
