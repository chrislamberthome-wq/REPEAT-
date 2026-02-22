# Link Protocol Spec v0.1

## Overview
The REPEAT link protocol defines how tiles are chained into a verifiable trace.

## Hash Chain
- `hash_chain[0]` is the genesis hash: `sha256:` + hex(SHA-256(`b"REPEAT:v0.1:genesis"`)).
- For each packet `i` (0-indexed):
  `hash_chain[i+1] = "sha256:" + hex(SHA-256( (hash_chain[i] + "|").encode() + c14n(packet[i]) ))`
  where `c14n` is the JCS canonical JSON bytes of the packet object.

## CRC Check
Every packet `crc16` field MUST equal CRC-16/CCITT-FALSE computed over the
UTF-8 encoding of the `payload` field.

## CRC-16/CCITT-FALSE Parameters
- Poly: 0x1021
- Init: 0xFFFF
- RefIn: False
- RefOut: False
- XorOut: 0x0000

## Fail-Closed
Any CRC mismatch, hash-chain break, or missing field is a hard FAIL.
