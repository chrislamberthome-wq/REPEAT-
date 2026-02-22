# B4IU Tile Spec v0.1

## Overview
A B4IU tile is the atomic compute unit in the REPEAT pipeline.
Each tile processes one link packet and emits identity-preserving output.

## Tile Fields
- `seq` (integer): zero-based sequence number within the run.
- `payload` (string): UTF-8 link payload string.
- `crc16` (integer): CRC-16/CCITT-FALSE over `payload` bytes.
- `ida_payload` (string): IDA annotation string for this tile.
- `ida_hash` (string): `sha256:` + hex(SHA-256(`ida_payload` UTF-8 bytes)).

## Canonicalization
All hash computation uses JCS / RFC 8785 (see `C14N_RULES.md`).

## Identity Invariant
`compute = memory = identity` holds when all CRC16 and IDA hash checks pass
and the hash chain is unbroken end-to-end.
