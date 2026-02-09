# Golden Test Vectors for Holo-ID v0

This directory contains golden test vectors for the Holo-ID v0 verification pipeline. Each golden packet is a pre-computed, known-good Holo-ID v0 packet that can be used for testing and validation.

## Golden Packets

### empty.json
- **Description**: Minimal packet with no data (empty string)
- **Data**: "" (empty)
- **Size**: 0 bytes
- **Use**: Test handling of empty data

### single_byte.json
- **Description**: Packet encoding a single ASCII character
- **Data**: "A"
- **Size**: 1 byte
- **Use**: Test minimal non-empty encoding

### hello.json
- **Description**: Packet encoding a greeting message
- **Data**: "Hello, Holo-ID v0!"
- **Size**: 18 bytes
- **Use**: Test typical text message encoding

### all_bytes.json
- **Description**: Packet encoding all possible byte values (0-255)
- **Data**: Binary sequence [0x00, 0x01, ..., 0xFF]
- **Size**: 256 bytes
- **Use**: Test full byte range encoding and ensure all geometric features are exercised

## Usage

### Verify a Golden Packet (Basic)
```bash
python src/verify_holo_id.py verify --input golden/hello.json
```

### Verify a Golden Packet (Strict)
```bash
python src/verify_holo_id.py verify --strict --input golden/hello.json
```

### Decode a Golden Packet
```bash
python src/verify_holo_id.py decode --input golden/hello.json
```

### Verify All Golden Packets
```bash
make golden
```

## Expected Behavior

All golden packets must:
1. Pass basic verification (checksum + schema validation)
2. Pass strict verification (all runtime invariants)
3. Round-trip correctly (decode then re-encode produces equivalent packet)

## Corruption Testing

Golden packets are also used as the basis for corruption testing:

```bash
# Simulate bit flip corruption
python src/verify_holo_id.py corrupt --input golden/hello.json --type bitflip --output corrupted.json

# Verify corrupted packet (should fail)
python src/verify_holo_id.py verify --input corrupted.json
```

## Regenerating Golden Packets

If the encoding scheme changes, regenerate golden packets:

```bash
echo -n "" | python src/verify_holo_id.py encode > golden/empty.json
echo -n "A" | python src/verify_holo_id.py encode > golden/single_byte.json
echo -n "Hello, Holo-ID v0!" | python src/verify_holo_id.py encode > golden/hello.json
python -c "import sys; sys.stdout.buffer.write(bytes(range(256)))" | python src/verify_holo_id.py encode > golden/all_bytes.json
```

## Timestamp Handling

Note that timestamps in golden packets reflect the time of generation. When testing, the verification process does NOT validate timestamps for freshness - it only validates the structure and checksum consistency.
