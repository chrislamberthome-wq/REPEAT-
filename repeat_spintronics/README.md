# REPEAT Spintronics MRAM MVP

## Overview

The REPEAT Spintronics MRAM MVP (Minimum Viable Product) implements the integration between Platoputer and spintronics using magnetization textures and cryptographic verification.

## Features

### 1. Magnetization Texture Encoding
- **Tetrahedron-based Codebooks**: Uses the tetrahedron as the minimal multi-state representation from the 5 Platonic solids framework
- **Binary to Magnetization**: Converts binary data to magnetization textures using 5-angle tuples (α_T, α_C, α_O, α_D, α_I)
- **Deterministic Encoding**: Produces consistent results for the same input

### 2. MRAM Packet Schema
- **Packet Format**: Standardized JSON schema (`packet.schema.json`) for write/read operations
- **Metadata**: Includes byte count, encoding method, and original data hash
- **Checksums**: SHA-256 checksums for packet integrity

### 3. Receipt Verification
- **SHA-based Proofs**: Cryptographic verification using SHA-256 hash chains
- **Verifier Proofs**: Multi-step proof chain that validates decode operations
- **Receipt Schema**: Standardized JSON schema (`receipt.schema.json`) for operation receipts

### 4. Deterministic Build/Init
- **Initialization Script**: `scripts/init_spintronics.py` provides deterministic verification
- **PASS Result**: All initialization checks pass with clear output

## Architecture

```
repeat_spintronics/
├── __init__.py           # Module exports
├── encoder.py            # Magnetization texture encoding/decoding
├── packetizer.py         # MRAM packet creation and verification
├── packet.schema.json    # JSON schema for packets
└── receipt.schema.json   # JSON schema for receipts
```

## Usage

### Encoding Data to Magnetization Textures

```python
from repeat_spintronics import encode_to_magnetization, decode_from_magnetization

# Encode binary data
data = b"Hello, MRAM!"
textures = encode_to_magnetization(data)

# Each texture is a 5-tuple: (α_T, α_C, α_O, α_D, α_I)
print(f"Generated {len(textures)} magnetization textures")

# Decode back to original data
decoded = decode_from_magnetization(textures)
assert decoded == data
```

### Creating MRAM Packets

```python
from repeat_spintronics import create_mram_packet, read_mram_packet

# Create a write packet
data = b"Important data"
packet = create_mram_packet(data, operation="write")

print(f"Packet ID: {packet['packet_id']}")
print(f"Textures: {len(packet['data']['textures'])}")
print(f"Checksum: {packet['checksum']}")

# Read data from packet
decoded = read_mram_packet(packet)
assert decoded == data
```

### Verifying Receipts

```python
from repeat_spintronics import create_mram_packet, verify_packet_receipt

# Create and verify a packet
packet = create_mram_packet(b"Verified data")
receipt = verify_packet_receipt(packet)

print(f"Receipt ID: {receipt['receipt_id']}")
print(f"Status: {receipt['status']}")
print(f"Verification: {receipt['verifier_proof']['verification_status']}")
print(f"Proof chain length: {len(receipt['verifier_proof']['proof_chain'])}")
```

### Complete Workflow

```python
from repeat_spintronics import (
    create_mram_packet,
    read_mram_packet,
    verify_packet_receipt,
)

# 1. Create MRAM packet
original_data = b"Complete workflow example"
packet = create_mram_packet(original_data, operation="write")

# 2. Read packet (simulate MRAM read operation)
decoded_data = read_mram_packet(packet)

# 3. Verify with receipt
receipt = verify_packet_receipt(packet, decoded_data)

# Check verification status
if receipt['status'] == 'success':
    print("✓ MRAM operation verified successfully")
    print(f"  Decoded {receipt['result']['decoded_bytes']} bytes")
    print(f"  Proof chain: {len(receipt['verifier_proof']['proof_chain'])} steps")
else:
    print("✗ Verification failed")
```

## Running Tests

```bash
# Run spintronics tests
PYTHONPATH=. python -m pytest tests/test_spintronics.py -v

# Run all tests
PYTHONPATH=. python -m pytest tests/ -v
```

## Initialization and Verification

Run the initialization script to verify the system:

```bash
PYTHONPATH=. python scripts/init_spintronics.py
```

Expected output:
```
============================================================
REPEAT Spintronics MRAM MVP - Initialization & Verification
============================================================

[1/5] Testing magnetization texture encoding...
  ✓ Encoding/decoding verified
[2/5] Testing MRAM packet creation...
  ✓ Packet created with all required fields
[3/5] Testing MRAM packet reading...
  ✓ Packet read successfully
[4/5] Testing verifier proof generation...
  ✓ Verifier proof generated and validated
[5/5] Testing schema compliance...
  ✓ Packet and receipt are JSON-serializable

============================================================
RESULT: PASS ✓
All tests passed. Spintronics MRAM MVP is operational.
============================================================
```

## Schema Specifications

### Packet Schema (`packet.schema.json`)
- **version**: Schema version (semver format)
- **packet_id**: Unique UUID v4 identifier
- **operation**: "write" or "read"
- **timestamp**: ISO 8601 timestamp
- **data**: Contains magnetization textures and metadata
- **checksum**: SHA-256 checksum of packet data

### Receipt Schema (`receipt.schema.json`)
- **version**: Schema version (semver format)
- **receipt_id**: Unique UUID v4 identifier
- **packet_id**: Reference to packet
- **operation**: "write" or "read"
- **timestamp**: ISO 8601 timestamp
- **status**: "success", "failure", or "pending"
- **verifier_proof**: SHA-based proof chain
- **result**: Operation result with decoded byte count

## Technical Details

### Encoding Method: `tetrahedron_5solids`

The encoding uses the 5 Platonic solids framework from `repeat_hd.codec_3d`:
- **Tetrahedron (T)**: Primary minimal multi-state indicator
- **Cube (C)**: Secondary state component
- **Octahedron (O)**: Tertiary state component
- **Dodecahedron (D)**: Quaternary state component
- **Icosahedron (I)**: Quinary state component

Each bit is encoded as a 5-angle tuple, and decoding uses majority voting (Rule A) for robustness.

### SHA-256 Verifier Proof Chain

The proof chain establishes cryptographic verification:
1. **Packet Hash**: SHA-256 of packet checksum
2. **Data Hash**: SHA-256 of decoded data
3. **Combined Hash**: SHA-256 of (packet_hash + data_hash)
4. **Original Hash Verification**: SHA-256 of original hash from metadata

This multi-step chain allows for probable decode verification and tamper detection.

## Dependencies

- Python 3.12+
- `repeat_hd` module (for `codec_3d` encoding primitives)

## License

See LICENSE file in the repository root.
