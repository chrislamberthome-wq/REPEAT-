# PublicHex v1 Specification

## Overview

PublicHex v1 is a hexadecimal encoding format for data frames that provides a standard way to represent binary data in a human-readable format with validation and normalization capabilities.

## Format Rules

### 1. Hexadecimal Encoding

- Data MUST be encoded as hexadecimal strings (base-16)
- Valid characters: `0-9`, `a-f`, `A-F`
- Both uppercase and lowercase hex digits are acceptable on input
- Canonical form uses lowercase hex digits (`a-f` for values 10-15)

### 2. Whitespace Handling

- Input MAY contain whitespace characters (spaces, tabs, newlines, carriage returns)
- Whitespace is ignored during parsing and removed during normalization
- Canonical form contains NO whitespace

### 3. Normalization

The normalization process transforms input hex strings to canonical form:

1. Remove all whitespace characters
2. Convert all hex digits to lowercase
3. Validate that only valid hex characters remain

### 4. Frame Structure

A PublicHex frame consists of:
- A header (8 bytes / 16 hex characters) containing:
  - CRC32 checksum (4 bytes / 8 hex characters)
  - Data length (4 bytes / 8 hex characters, little-endian)
- Payload data (variable length)

### 5. Validation

A frame is considered VALID if:
- It contains only valid hexadecimal characters (after whitespace removal)
- The length is at least 16 hex characters (8 bytes for header)
- The data length field matches the actual payload length
- The CRC32 checksum matches the payload data

A frame is considered INVALID if:
- It contains non-hexadecimal characters (excluding whitespace)
- It is too short (< 16 hex characters)
- The length field does not match the payload length
- The CRC32 checksum does not match the payload data

## Canonical JSON Capsule

The canonical JSON output format for a PublicHex frame verification is:

```json
{
  "encoding": "publichex-v1",
  "normalized_frame_hex": "<lowercase_hex_string_without_whitespace>"
}
```

### Fields

- **encoding** (string): MUST be `"publichex-v1"` to indicate this specification version
- **normalized_frame_hex** (string): The canonical form of the frame (lowercase, no whitespace)

### Error Reporting

In addition to the canonical JSON output on stdout, error details are written to stderr as JSON when validation fails:

**For parse errors (exit code 1):**
```json
{
  "encoding": "publichex-v1",
  "normalized_frame_hex": "",
  "errors": ["error message"]
}
```
Written to stderr.

**For validation failures (exit code 2):**
Canonical JSON is written to stdout, and error details are written to stderr:
```json
{
  "errors": ["error message"]
}
```

### Exit Codes

The verification process uses the following exit codes:

- **0 (PASS)**: Frame is valid and all checks passed
- **2 (FAIL)**: Frame structure is parseable but validation failed (CRC/length mismatch)
- **1 (ERROR)**: Parse error or usage error (invalid hex, wrong format, missing arguments)

## Examples

### Valid Frame (PASS)

Input (with whitespace):
```
8289 D1F7
0500 0000
4865 6C6C 6F
```

Canonical output:
```json
{
  "encoding": "publichex-v1",
  "normalized_frame_hex": "8289d1f70500000048656c6c6f"
}
```

### Invalid Frame (FAIL)

Input (CRC mismatch):
```
FFFFFFFF0500000048656c6c6f
```

Canonical output (normalized, but fails validation):
```json
{
  "encoding": "publichex-v1",
  "normalized_frame_hex": "ffffffff0500000048656c6c6f"
}
```
Exit code: 2 (FAIL)

### Parse Error (ERROR)

Input (non-hex characters):
```
G1H2I3J4
```

Exit code: 1 (ERROR)

## Version History

- **v1 (2026-01-28)**: Initial specification
