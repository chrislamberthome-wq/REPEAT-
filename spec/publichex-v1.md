# PublicHex v1 Specification

## Overview

PublicHex is a hexadecimal encoding format for representing data frames in a standardized, canonical way. This specification defines the rules for PublicHex v1, including validation criteria and canonical representation.

## Canonical JSON Capsule Definition

A valid PublicHex v1 capsule is represented as a JSON object with the following structure:

```json
{
  "encoding": "publichex-v1",
  "normalized_frame_hex": "<lowercase hexadecimal string>"
}
```

### Fields

- **encoding** (string, required): Must be exactly `"publichex-v1"`
- **normalized_frame_hex** (string, required): A lowercase hexadecimal string with no whitespace

## Validation Rules

### PASS Criteria

A hexadecimal input passes PublicHex v1 validation if:

1. It contains only valid hexadecimal characters (0-9, a-f, A-F) and whitespace
2. After removing whitespace and converting to lowercase, it produces a valid hexadecimal string
3. The resulting string has an even number of characters (represents complete bytes)

### FAIL Criteria

A hexadecimal input fails PublicHex v1 validation if:

1. It contains non-hexadecimal, non-whitespace characters
2. After removing whitespace, it has an odd number of characters
3. The input is empty or contains only whitespace

## Normalization Process

The normalization process transforms any valid hexadecimal input into its canonical form:

1. Remove all whitespace characters (spaces, tabs, newlines, etc.)
2. Convert all alphabetic hexadecimal characters to lowercase
3. Validate that the result contains only characters in the set [0-9a-f]
4. Validate that the result has an even number of characters

## Examples

### PASS Examples

Input: `"48656C6C6F"`
Normalized: `"48656c6c6f"`

Input: `"48 65 6C 6C 6F"`
Normalized: `"48656c6c6f"`

Input: `"48656C\n6C6F"`
Normalized: `"48656c6c6f"`

Input: `"DEADBEEF"`
Normalized: `"deadbeef"`

### FAIL Examples

Input: `"48656C6C6G"` (invalid character 'G')
Reason: Contains non-hexadecimal character

Input: `"48656C6C6"` (odd length)
Reason: Odd number of characters

Input: `""` (empty)
Reason: Empty input

Input: `"   "` (whitespace only)
Reason: No hexadecimal content

## Exit Codes

When using the `publichex-verify` command:

- **0 (PASS)**: Input is valid PublicHex v1
- **2 (FAIL)**: Input fails PublicHex v1 validation
- **1 (ERROR)**: Parse error or incorrect usage

## Version History

- **v1** (2026-01-28): Initial specification
