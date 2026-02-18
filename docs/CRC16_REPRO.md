# CRC-16/CCITT-FALSE Reproduction

This document describes how to reproduce the CRC-16/CCITT-FALSE golden vector validation.

## Golden Vector

The implementation validates the following golden vector:
- **Payload**: `"F0|ABC|3|1"`
- **Expected CRC**: `0x34B6`

## Algorithm Parameters

- **Polynomial**: 0x1021
- **Initial value**: 0xFFFF
- **Input reflection**: false
- **Output reflection**: false
- **Final XOR**: 0x0000

## Usage

### Python Implementation

#### Print CRC value (stdin mode)
```bash
# Python mirror (prints 0x34B6)
echo -n "F0|ABC|3|1" | python3 tools/crc16_ccitt_false.py
```

#### Calculate CRC with payload argument
```bash
python3 tools/crc16_ccitt_false.py --payload "F0|ABC|3|1"
```

#### Validation mode (PASS/NACK)
```bash
# PASS/NACK mode
python3 tools/crc16_ccitt_false.py --payload "F0|ABC|3|1" --expect 0x34B6
```

## Testing

Run the unit tests to verify the golden vector:
```bash
PYTHONPATH=. python3 -m unittest -v tests.test_crc16_golden
```

## Makefile Targets

The following Makefile targets are available:

```bash
# Run CRC calculation
make crc16-py-run

# Run unit tests
make crc16-py-test
```
