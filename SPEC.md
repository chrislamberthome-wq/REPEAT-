# Holo-ID v0 Specification

## Overview

Holo-ID v0 is a REPEAT-verifiable encoding system that uses geometric representations of the icosidodecahedron boundary to encode and verify audit log data. This specification defines the encoding scheme, verification procedures, and data structures for Holo-ID v0.

## 1. Introduction

### 1.1 Purpose

Holo-ID v0 provides a geometric encoding system for audit logs with built-in verification capabilities. It leverages the icosidodecahedron's 32 faces (20 triangular and 12 pentagonal) as a canonical boundary for encoding data.

### 1.2 Design Goals

- **Verifiability**: All encoded data must be verifiable through geometric consistency checks
- **Repeatability**: Encoding and decoding operations must be deterministic and repeatable
- **Tamper Detection**: Any corruption or modification should be detectable through geometric invariants
- **Self-Auditing**: Runtime invariant checks provide additional verification beyond basic checksums

## 2. Geometric Foundation

### 2.1 Icosidodecahedron Properties

The icosidodecahedron is an Archimedean solid with the following properties:
- **Vertices**: 30 vertices
- **Edges**: 60 edges
- **Faces**: 32 faces (20 triangular + 12 pentagonal)
- **Vertex Coordinates**: All vertices lie at unit distance from the center
- **Symmetry Group**: Full icosahedral symmetry (Ih)

### 2.2 Canonical Representation

The canonical icosidodecahedron boundary is defined with:
- Unit radius sphere (r = 1.0)
- Vertices positioned using golden ratio φ = (1 + √5) / 2
- Standard orientation aligned with coordinate axes

### 2.3 Coordinate System

Vertices are expressed in Cartesian coordinates (x, y, z) where:
- All vertex coordinates are normalized to unit sphere
- Coordinates use the golden ratio: φ ≈ 1.618034
- The inverse golden ratio: 1/φ ≈ 0.618034

## 3. Encoding Scheme

### 3.1 Data to Geometry Mapping

Binary data is encoded using the following mapping:

1. **Byte Extraction**: Input data is read as a sequence of bytes
2. **Vertex Selection**: Each byte (0-255) maps to a geometric feature:
   - Low values (0-29): Direct vertex indices
   - Mid values (30-89): Edge midpoints
   - High values (90-255): Face centers or composite positions
3. **Coordinate Generation**: Selected features produce (x, y, z) coordinates
4. **Packet Formation**: Coordinates are packaged with metadata

### 3.2 Packet Structure

Each Holo-ID v0 packet contains:

```
{
  "version": "v0",
  "timestamp": <ISO 8601 timestamp>,
  "data": <base64-encoded binary data>,
  "geometry": {
    "boundary": "icosidodecahedron",
    "coordinates": [<list of [x, y, z] points>]
  },
  "checksum": {
    "algorithm": "CRC32",
    "value": <hex string>
  }
}
```

### 3.3 Metadata Fields

- **version**: Protocol version identifier (always "v0" for this specification)
- **timestamp**: UTC timestamp in ISO 8601 format
- **data**: Base64-encoded original binary data
- **geometry.boundary**: Geometric boundary type (always "icosidodecahedron")
- **geometry.coordinates**: List of 3D coordinates corresponding to encoded data
- **checksum.algorithm**: Checksum algorithm used (CRC32)
- **checksum.value**: Hexadecimal checksum of the data

## 4. Verification Procedures

### 4.1 Basic Verification

Basic verification includes:

1. **Checksum Validation**: Verify CRC32 checksum matches data
2. **Schema Validation**: Ensure packet structure conforms to JSON schema
3. **Boundary Validation**: Confirm all coordinates lie on icosidodecahedron boundary

### 4.2 Strict Verification

Strict verification adds runtime invariant checks:

1. **Re-encoding Consistency**: Re-encoding decoded data produces identical geometry
2. **Coordinate Validation**: All coordinates must lie on unit sphere within tolerance
3. **Symmetry Preservation**: Encoded geometry respects icosahedral symmetry
4. **Length Consistency**: Number of coordinates matches data length

### 4.3 Tolerance Parameters

- **Coordinate Tolerance**: ε = 1e-6 for floating-point comparisons
- **Radius Tolerance**: δ = 1e-5 for unit sphere validation
- **Angle Tolerance**: θ = 1e-4 radians for geometric relationships

## 5. Corruption Simulation

### 5.1 Types of Corruption

Holo-ID v0 supports simulation of the following corruption types:

1. **Bit Flip**: Random bit flips in binary data
2. **Coordinate Perturbation**: Small random changes to coordinate values
3. **Checksum Mismatch**: Altered checksum without data change
4. **Geometry Mismatch**: Coordinates inconsistent with data encoding

### 5.2 Corruption Detection

Each corruption type should be detectable through:
- **Bit Flip**: Checksum validation fails
- **Coordinate Perturbation**: Boundary validation fails
- **Checksum Mismatch**: Checksum validation fails
- **Geometry Mismatch**: Re-encoding consistency check fails

## 6. Implementation Requirements

### 6.1 Command-Line Interface

The implementation must provide a CLI with the following commands:

```bash
# Encode data to Holo-ID v0 packet
verify_holo_id.py encode --input <file> --output <packet.json>

# Decode Holo-ID v0 packet to original data
verify_holo_id.py decode --input <packet.json> --output <file>

# Verify Holo-ID v0 packet
verify_holo_id.py verify --input <packet.json> [--strict]

# Simulate corruption
verify_holo_id.py corrupt --input <packet.json> --type <corruption_type> --output <corrupted.json>
```

### 6.2 Exit Codes

- **0**: Success / verification passed
- **1**: Failure / verification failed (checksum or parse error)
- **2**: Invariant check failed (strict mode only)

### 6.3 Error Handling

The implementation must handle:
- Invalid JSON input
- Missing required fields
- Out-of-range coordinate values
- Checksum mismatches
- Schema validation errors

## 7. Test Vectors

### 7.1 Golden Packets

Golden packets are pre-computed test vectors with known correct outputs:

1. **Empty Data**: Minimal packet with no data
2. **Single Byte**: Packet encoding a single byte
3. **ASCII String**: Packet encoding "Hello, Holo-ID v0!"
4. **Binary Data**: Packet encoding random binary data

### 7.2 Verification Test Cases

Each golden packet must pass:
- Basic verification (checksum + schema)
- Strict verification (all invariants)
- Round-trip encoding/decoding

### 7.3 Corruption Test Cases

Corrupted versions of golden packets must fail verification with appropriate error codes.

## 8. Schema Definition

The JSON schema for Holo-ID v0 packets is defined in `schema/holo-id-v0.schema.json` and enforces:
- Required fields and their types
- Coordinate array structure
- Checksum format
- Version constraints

## 9. Security Considerations

### 9.1 Tamper Evidence

The geometric encoding provides tamper evidence through:
- Checksum validation
- Geometric consistency checks
- Symmetry preservation requirements

### 9.2 Limitations

Holo-ID v0 does not provide:
- Cryptographic authentication
- Encryption of data
- Protection against replay attacks

### 9.3 Recommended Practices

For production use:
- Combine with cryptographic signatures
- Use secure channels for packet transmission
- Implement timestamp validation
- Store packets in append-only logs

## 10. Version History

### v0 (Initial Release)

- Basic encoding/decoding using icosidodecahedron boundary
- CRC32 checksum validation
- Strict mode with runtime invariants
- JSON packet format
- Corruption simulation support

## 11. References

- Archimedean Solids: Mathematical properties and coordinates
- CRC32 Algorithm: IEEE 802.3 standard
- JSON Schema: Draft 2020-12
- ISO 8601: Date and time format standard

## Appendix A: Icosidodecahedron Vertices

The 30 vertices of the canonical icosidodecahedron are defined in `boundary/icosidodecahedron_canonical.json`.

## Appendix B: Example Usage

### Basic Workflow

```bash
# Create audit log entry
echo "System event: User login at 2026-02-09T23:48:00Z" > event.txt

# Encode to Holo-ID v0 packet
python src/verify_holo_id.py encode --input event.txt --output event.json

# Verify packet (basic)
python src/verify_holo_id.py verify --input event.json

# Verify packet (strict)
python src/verify_holo_id.py verify --input event.json --strict

# Simulate corruption
python src/verify_holo_id.py corrupt --input event.json --type bitflip --output corrupted.json

# Verify corrupted packet (should fail)
python src/verify_holo_id.py verify --input corrupted.json
```

### Integration with CI/CD

```bash
# Run smoke tests
make smoke

# Verify golden packets
make golden

# Run full verification suite
make verify
```
