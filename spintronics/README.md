# Spintronics REPEAT + Platoputer Protocol

This module implements a spintronics-ready REPEAT + Platoputer protocol with MRAM MVP (Minimum Viable Product) for fast scientific adoption.

## Quick Start

```bash
# Run the demonstration script
python scripts/demo_spintronics.py

# Verify example packets
python -m spintronics.verifiers.verify_mram_write_read \
  spintronics/examples/example_mram_receipt.json

python -m spintronics.verifiers.verify_state_survival_macrospin \
  spintronics/examples/example_spin_configuration.json

python -m spintronics.verifiers.verify_trace_integrity \
  spintronics/examples/example_pulse_trace.json

# Run tests
pytest tests/test_spintronics*.py -v
```

## Overview

The spintronics protocol provides a standardized framework for experimental packet handling, verification, and data integrity in spintronics research, with a focus on MRAM (Magnetoresistive Random Access Memory) applications.

## Features

### 1. JSON Schema Definitions

Three comprehensive schemas for spintronics experimental packets:

- **`state_survival_macrospin_v1.schema.json`**: Spin configuration packets with nearest neighbor decoding
  - 2D spin lattice representation
  - Nearest neighbor interaction parameters
  - Experimental metadata (temperature, field, evolution time)

- **`trace_integrity_v1.schema.json`**: Pulse-trace validity verification
  - Pulse sequence specification
  - Integrity checksums (SHA-256, CRC32, MD5)
  - Trace timing metadata

- **`mram_write_read_v1.schema.json`**: Threshold-based MRAM state flipping
  - Write operation with pulse programming
  - Read operation with resistance measurement
  - Threshold verification and TMR calculation

### 2. Core Python Modules

- **`canonical.py`**: JSON canonicalization for consistent hashing
  - Deterministic JSON serialization
  - Canonical form validation
  - Packet normalization

- **`hash.py`**: Cryptographic hashing for receipts and traces
  - Packet hashing (SHA-256, MD5, SHA-1)
  - Trace sequence hashing
  - Receipt hash computation
  - Checksum verification

### 3. Verification Scripts

Three specialized verifiers in the `verifiers/` package:

- **`verify_state_survival_macrospin.py`**: Spin state verification
  - Validates spin configuration structure
  - Computes nearest neighbor energy
  - Checks state survival criteria
  - Usage: `python -m spintronics.verifiers.verify_state_survival_macrospin <packet.json>`

- **`verify_trace_integrity.py`**: Pulse trace verification
  - Validates pulse sequence structure
  - Verifies integrity checksums
  - Checks timing consistency
  - Usage: `python -m spintronics.verifiers.verify_trace_integrity <trace.json>`

- **`verify_mram_write_read.py`**: MRAM operation verification
  - Validates threshold parameters
  - Verifies write/read consistency
  - Checks resistance-to-bit decoding
  - Usage: `python -m spintronics.verifiers.verify_mram_write_read <receipt.json>`

## Installation

The spintronics module is part of the REPEAT- repository. Install dependencies:

```bash
pip install -r requirements-dev.txt
```

## Usage Examples

### 1. Verifying Example Packets

```bash
# Verify spin configuration
python -m spintronics.verifiers.verify_state_survival_macrospin \
  spintronics/examples/example_spin_configuration.json

# Verify pulse trace
python -m spintronics.verifiers.verify_trace_integrity \
  spintronics/examples/example_pulse_trace.json

# Verify MRAM receipt
python -m spintronics.verifiers.verify_mram_write_read \
  spintronics/examples/example_mram_receipt.json
```

### 2. Using Core Modules

```python
from spintronics import hash_packet, canonicalize_json
from spintronics.verifiers import verify_mram_write_read

# Create and hash a packet
packet = {
    "id": "test",
    "data": [1, 2, 3]
}
packet_hash = hash_packet(packet)
print(f"Packet hash: {packet_hash}")

# Canonicalize JSON
canonical = canonicalize_json(packet)
print(f"Canonical form: {canonical}")

# Verify MRAM receipt
with open("receipt.json") as f:
    receipt = json.load(f)
is_valid, details = verify_mram_write_read(receipt)
print(f"Valid: {is_valid}, Details: {details}")
```

### 3. Calibration and Testing

Open the calibration notebook to explore threshold models:

```bash
jupyter notebook spintronics/mram_calibration.ipynb
```

The notebook covers:
- Threshold model calibration
- Resistance distribution simulation
- Drift detection over time
- Test data generation
- Threshold optimization

## Directory Structure

```
spintronics/
├── __init__.py                 # Module initialization
├── canonical.py                # JSON canonicalization
├── hash.py                     # Hashing utilities
├── README.md                   # This file
├── mram_calibration.ipynb      # Calibration notebook
├── schemas/                    # JSON schemas
│   ├── state_survival_macrospin_v1.schema.json
│   ├── trace_integrity_v1.schema.json
│   └── mram_write_read_v1.schema.json
├── verifiers/                  # Verification scripts
│   ├── __init__.py
│   ├── verify_state_survival_macrospin.py
│   ├── verify_trace_integrity.py
│   └── verify_mram_write_read.py
└── examples/                   # Example packets
    ├── README.md
    ├── example_spin_configuration.json
    ├── example_pulse_trace.json
    └── example_mram_receipt.json
```

## Testing

Run the test suite:

```bash
pytest tests/test_spintronics*.py -v
```

Tests cover:
- Canonical JSON serialization
- Hash computation and verification
- Verifier functionality
- Edge cases and error handling

## MRAM Threshold Model

The MRAM verification uses a threshold-based resistance decoding model:

### Theory

- **Parallel state (P)**: Low resistance R_P ≈ 2kΩ → bit 0
- **Antiparallel state (AP)**: High resistance R_AP ≈ 5kΩ → bit 1
- **TMR ratio**: TMR = (R_AP - R_P) / R_P ≈ 1.5

### Threshold Decoding

```
Midpoint threshold = (R_P + R_AP) / 2 = 3.5kΩ

If measured_resistance < threshold → bit 0
If measured_resistance > threshold → bit 1
```

### Switching Margin

The switching margin ensures robust state detection:

```
Margin = R_AP - R_P = 3kΩ
```

For reliable operation, maintain margin > 2kΩ.

## Scientific Applications

This protocol is designed for:

1. **MRAM characterization**: Write/read cycle validation, threshold calibration
2. **Spintronics research**: Spin dynamics, state survival analysis
3. **Pulse programming**: Trace integrity, timing validation
4. **Data integrity**: Cryptographic receipts, tamper detection
5. **Calibration workflows**: Drift monitoring, threshold optimization

## Schema Compliance

All packets must validate against their respective JSON schemas. Use a JSON schema validator or the provided verification scripts to ensure compliance.

Example schema validation with Python:

```python
import json
import jsonschema

# Load schema
with open("schemas/mram_write_read_v1.schema.json") as f:
    schema = json.load(f)

# Load and validate packet
with open("examples/example_mram_receipt.json") as f:
    packet = json.load(f)
    
jsonschema.validate(packet, schema)
print("Packet is valid!")
```

## Contributing

When adding new features:

1. Update appropriate JSON schemas
2. Add verification logic to verifiers
3. Create example packets demonstrating new features
4. Add comprehensive tests
5. Update documentation

## License

See LICENSE file in the root directory.

## References

- MRAM Technology: Magnetoresistive Random Access Memory
- TMR Effect: Tunnel Magnetoresistance
- Spintronics: Spin-based electronics
- JSON Schema: http://json-schema.org/
